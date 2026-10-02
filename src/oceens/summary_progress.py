"""Progress reporting for the asynchronous summary queue."""

from dataclasses import dataclass

from sqlalchemy import func
from sqlmodel import Session, select

from oceens.models import Summary


@dataclass(frozen=True)
class SurveyProgress:
    """Aggregated summary job counts and a fixed-rate remaining-time estimate."""

    done: int
    total: int
    errors: int
    estimated_seconds_left: int
    finished: bool


def progress(
    session: Session, survey_id: int, seconds_per_job: int = 20
) -> SurveyProgress:
    """Return progress for one survey, estimating pending jobs at a fixed rate.

    A status of 0 is pending, 200 is successful, and every other status is an
    error. The estimate deliberately uses only the pending count and the
    caller-provided rate; it does not inspect job metadata or the clock.
    """
    status_counts = session.exec(
        select(Summary.http_status, func.count())
        .where(Summary.survey_id == survey_id)
        .group_by(Summary.http_status)
    ).all()

    pending = 0
    done = 0
    errors = 0
    for status, count in status_counts:
        if status == 0:
            pending += count
        elif status == 200:
            done += count
        else:
            errors += count

    total = pending + done + errors
    finished = total > 0 and pending == 0
    queue_pending = session.exec(
        select(func.count()).select_from(Summary).where(Summary.http_status == 0)
    ).one()
    return SurveyProgress(
        done=done,
        total=total,
        errors=errors,
        estimated_seconds_left=(
            0 if finished else queue_pending * seconds_per_job
        ),
        finished=finished,
    )
