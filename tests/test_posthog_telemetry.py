"""PostHog is optional locally and must be configured as one complete group."""

import logging
from contextlib import nullcontext

import pytest

import posthog
import oceens.posthog_telemetry as telemetry


def test_posthog_is_disabled_when_every_setting_is_empty():
    assert telemetry.read_posthog_settings({}) is None
    assert telemetry.read_posthog_settings(
        {
            "POSTHOG_PROJECT_TOKEN": "",
            "POSTHOG_HOST": "  ",
            "POSTHOG_ENVIRONMENT": "",
        }
    ) is None


def test_partial_posthog_settings_name_the_missing_setting():
    with pytest.raises(ValueError, match="POSTHOG_ENVIRONMENT missing"):
        telemetry.read_posthog_settings(
            {
                "POSTHOG_PROJECT_TOKEN": "phc-test-token",
                "POSTHOG_HOST": "https://eu.i.posthog.com",
            }
        )


def test_posthog_settings_are_normalized():
    settings = telemetry.read_posthog_settings(
        {
            "POSTHOG_PROJECT_TOKEN": " phc-test-token ",
            "POSTHOG_HOST": " https://eu.i.posthog.com/ ",
            "POSTHOG_ENVIRONMENT": " staging ",
        }
    )

    assert settings == telemetry.PostHogSettings(
        project_token="phc-test-token",
        host="https://eu.i.posthog.com",
        environment="staging",
    )


def test_start_telemetry_wires_project_environment_and_otlp_logs(monkeypatch):
    created = {}

    class FakeClient:
        def __init__(self, token, **kwargs):
            created["client"] = (token, kwargs)
            self.closed = False

        def shutdown(self):
            self.closed = True

    class FakeExporter:
        def __init__(self, **kwargs):
            created["exporter"] = kwargs

    class FakeProvider:
        def __init__(self, resource):
            created["resource"] = resource.attributes
            self.processors = []
            self.closed = False

        def add_log_record_processor(self, processor):
            self.processors.append(processor)

        def shutdown(self):
            self.closed = True

    class FakeProcessor:
        def __init__(self, exporter):
            self.exporter = exporter

    class FakeHandler(logging.Handler):
        def __init__(self, level, logger_provider):
            super().__init__(level)
            self.logger_provider = logger_provider

    monkeypatch.setattr(telemetry, "Posthog", FakeClient)
    monkeypatch.setattr(telemetry, "OTLPLogExporter", FakeExporter)
    monkeypatch.setattr(telemetry, "LoggerProvider", FakeProvider)
    monkeypatch.setattr(telemetry, "BatchLogRecordProcessor", FakeProcessor)
    monkeypatch.setattr(telemetry, "LoggingHandler", FakeHandler)

    root = logging.getLogger()
    original_level = root.level
    original_handlers = root.handlers[:]
    service_logger = logging.getLogger("oceens.telemetry-test")
    original_propagate = service_logger.propagate
    original_service_handlers = service_logger.handlers[:]
    service_logger.propagate = False
    try:
        active = telemetry.start_telemetry(
            telemetry.PostHogSettings(
                "phc-test-token", "https://eu.i.posthog.com", "staging"
            ),
            "oceens-summaries",
            logger_names=("oceens.telemetry-test",),
        )

        assert active is not None
        assert created["client"] == (
            "phc-test-token",
            {
                "host": "https://eu.i.posthog.com",
                "enable_exception_autocapture": True,
                "super_properties": {"environment": "staging"},
            },
        )
        assert created["exporter"] == {
            "endpoint": "https://eu.i.posthog.com/i/v1/logs",
            "headers": {"Authorization": "Bearer phc-test-token"},
        }
        assert created["resource"]["service.name"] == "oceens-summaries"
        assert created["resource"]["deployment.environment"] == "staging"
        assert active.logging_handler in root.handlers
        assert active.logging_handler in service_logger.handlers

        active.shutdown()

        assert active.client.closed
        assert active.logger_provider.closed
        assert active.logging_handler not in root.handlers
        assert active.logging_handler not in service_logger.handlers
    finally:
        root.handlers[:] = original_handlers
        root.setLevel(original_level)
        service_logger.handlers[:] = original_service_handlers
        service_logger.propagate = original_propagate


def test_web_request_context_identifies_the_signed_in_user(monkeypatch):
    import asyncio
    from starlette.requests import Request
    from starlette.responses import Response

    from oceens import main

    app = main.create_app()
    app.state.posthog_client = object()
    identified = []
    saw_session = []
    monkeypatch.setattr(
        main,
        "get_current_user",
        lambda request: (
            saw_session.append("session" in request.scope)
            or {"email": "student@example.edu"}
        ),
    )
    monkeypatch.setattr(posthog, "new_context", lambda client: nullcontext())
    monkeypatch.setattr(posthog, "identify_context", identified.append)

    posthog_middleware = next(
        middleware
        for middleware in app.user_middleware
        if middleware.kwargs.get("dispatch")
        and middleware.kwargs["dispatch"].__name__ == "posthog_request_context"
    )
    session_middleware_index = next(
        index
        for index, middleware in enumerate(app.user_middleware)
        if middleware.cls.__name__ == "SessionMiddleware"
    )
    posthog_middleware_index = app.user_middleware.index(posthog_middleware)
    assert session_middleware_index < posthog_middleware_index

    request = Request(
        {
            "type": "http",
            "app": app,
            "session": {},
            "method": "GET",
            "path": "/",
            "headers": [],
        }
    )

    async def run_middleware():
        async def call_next(request):
            return Response("ok")

        return await posthog_middleware.kwargs["dispatch"](request, call_next)

    response = asyncio.run(run_middleware())

    assert response.status_code == 200
    assert saw_session and all(saw_session)
    assert identified == ["student@example.edu"]


def test_summaries_context_identifies_daemon_and_tags_survey(monkeypatch):
    from contextlib import nullcontext

    from oceens import summaries_generator_daemon as daemon

    identities = []
    tags = []
    monkeypatch.setattr(posthog, "new_context", lambda client: nullcontext())
    monkeypatch.setattr(posthog, "identify_context", identities.append)
    monkeypatch.setattr(posthog, "tag", lambda name, value: tags.append((name, value)))

    with daemon._posthog_context(object(), survey_id=17):
        pass

    assert identities == ["oceens-summaries"]
    assert tags == [("survey_id", 17)]
