"""Opt-in PostHog error tracking and OTLP log export for each process."""

from dataclasses import dataclass
import logging
import os
from typing import Mapping

from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs._internal import LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from posthog import Posthog


# Set by the process lifespan/main, never by import or the SDK global client.
_process_client: Posthog | None = None


def capture_exception(error: BaseException) -> None:
    """Report a caught failure in the current request/survey context, if enabled."""
    client = _process_client
    if client is None:
        return
    try:
        client.capture_exception(error)
    except Exception:
        # Telemetry must not change a rollback, fallback or HTTP response.
        # Keep the export failure's details out of logs (they may contain secrets).
        logging.getLogger(__name__).warning("PostHog could not report a caught exception")


@dataclass(frozen=True)
class PostHogSettings:
    project_token: str
    host: str
    environment: str


@dataclass
class Telemetry:
    client: Posthog
    logger_provider: LoggerProvider
    logging_handler: LoggingHandler
    attached_loggers: tuple[logging.Logger, ...]

    def shutdown(self) -> None:
        """Detach and flush telemetry providers before the process exits."""
        global _process_client
        if _process_client is self.client:
            _process_client = None
        for logger in self.attached_loggers:
            logger.removeHandler(self.logging_handler)
        self.logger_provider.shutdown()
        self.client.shutdown()


def read_posthog_settings(
    environ: Mapping[str, str] | None = None,
) -> PostHogSettings | None:
    """Return complete PostHog settings, or disable telemetry when all are empty."""
    values = os.environ if environ is None else environ
    names = ("POSTHOG_PROJECT_TOKEN", "POSTHOG_HOST", "POSTHOG_ENVIRONMENT")
    configured = {name: (values.get(name) or "").strip() for name in names}
    if not any(configured.values()):
        return None

    missing = [name for name, value in configured.items() if not value]
    if missing:
        raise ValueError(f"{', '.join(missing)} missing")

    return PostHogSettings(
        project_token=configured["POSTHOG_PROJECT_TOKEN"],
        host=configured["POSTHOG_HOST"].rstrip("/"),
        environment=configured["POSTHOG_ENVIRONMENT"],
    )


def start_telemetry(
    settings: PostHogSettings | None,
    service_name: str,
    logger_names: tuple[str, ...],
) -> Telemetry | None:
    """Start PostHog and OTLP logging only when all settings are configured."""
    global _process_client
    if settings is None:
        _process_client = None
        return None

    client = Posthog(
        settings.project_token,
        host=settings.host,
        enable_exception_autocapture=True,
        super_properties={"environment": settings.environment},
    )
    provider = LoggerProvider(
        resource=Resource.create(
            {
                "service.name": service_name,
                "deployment.environment": settings.environment,
            }
        )
    )
    exporter = OTLPLogExporter(
        endpoint=f"{settings.host}/i/v1/logs",
        headers={"Authorization": f"Bearer {settings.project_token}"},
    )
    provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=provider)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    loggers = [root_logger]
    for name in logger_names:
        logger = logging.getLogger(name)
        if not logger.propagate:
            loggers.append(logger)
    for logger in loggers:
        logger.addHandler(handler)

    _process_client = client
    return Telemetry(client, provider, handler, tuple(loggers))
