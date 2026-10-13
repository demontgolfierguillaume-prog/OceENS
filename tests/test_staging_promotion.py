"""Promotion must follow staging's deployment result, including across pages."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "find_staging_image", Path(__file__).parents[1] / "scripts" / "find_staging_image.py"
)
promotion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(promotion)


def run(run_id, sha, conclusion="success"):
    return {"id": run_id, "head_sha": sha, "html_url": f"https://github.com/example/runs/{run_id}",
            "conclusion": conclusion}


def test_failed_latest_deploy_is_skipped_even_when_run_succeeded():
    messages = []

    def get_page(path):
        if "/workflows/" in path:
            return {"workflow_runs": [run(3, "new"), run(2, "tested", "failure")]}
        return {"jobs": [{"name": "deploy to staging", "conclusion":
                          "failure" if "/runs/3/" in path else "success"}]}

    image = promotion.find_staging_image("Student/OceENS", "default", get_page, messages.append)
    assert image == "ghcr.io/student/oceens:tested"
    assert any("Skipped run 3" in message for message in messages)


def test_older_success_can_be_on_a_later_page():
    def get_page(path):
        if "/workflows/" in path:
            return {"workflow_runs": [run(2, "red")] if path.endswith("&page=1") else [run(1, "green")]}
        return {"jobs": [{"name": "deploy to staging", "conclusion":
                          "cancelled" if "/runs/2/" in path else "success"}]}

    assert promotion.find_staging_image("student/oceens", "default", get_page).endswith(":green")


def test_no_successful_staging_deploy_refuses_promotion():
    def get_page(path):
        if "/workflows/" in path:
            return {"workflow_runs": [run(1, "pending")] if path.endswith("&page=1") else []}
        return {"jobs": [{"name": "architecture", "conclusion": "success"}]}

    with pytest.raises(RuntimeError, match="nothing to promote"):
        promotion.find_staging_image("student/oceens", "default", get_page)
