from sqlmodel import Session, SQLModel, create_engine


def test_progress_reports_pending_jobs_and_estimated_time():
    # Import all table models so SQLModel can create the foreign-key tables.
    from oceens import models  # noqa: F401
    from oceens.models import Summary, Survey

    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        survey = Survey()
        session.add(survey)
        session.commit()
        session.refresh(survey)

        other_survey = Survey()
        session.add(other_survey)
        session.commit()
        session.refresh(other_survey)
        session.add_all(
            [Summary(survey_id=survey.survey_id, http_status=0) for _ in range(45)]
            + [Summary(survey_id=other_survey.survey_id, http_status=0) for _ in range(45)]
        )
        session.commit()

        # Import inside the test so a missing implementation is a normal test
        # failure, rather than a test collection error.
        from oceens.summary_progress import progress

        result = progress(session, survey.survey_id)

    assert result.total == 45
    assert result.done == 0
    assert result.errors == 0
    assert result.finished is False
    assert result.estimated_seconds_left == 1800

    with Session(engine) as session:
        from oceens.summary_progress import progress

        result = progress(session, survey.survey_id, seconds_per_job=120)
        assert result.estimated_seconds_left == 10800


def test_progress_counts_successes_errors_and_ignores_other_surveys():
    from oceens import models  # noqa: F401
    from oceens.models import Summary, Survey

    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        survey = Survey()
        other_survey = Survey()
        session.add_all([survey, other_survey])
        session.commit()
        session.refresh(survey)
        session.refresh(other_survey)
        session.add_all(
            [Summary(survey_id=survey.survey_id, http_status=200) for _ in range(39)]
            + [Summary(survey_id=survey.survey_id, http_status=200, summary_text=None)]
            + [Summary(survey_id=survey.survey_id, http_status=504) for _ in range(5)]
            + [Summary(survey_id=other_survey.survey_id, http_status=0)]
        )
        session.commit()

        from oceens.summary_progress import progress

        result = progress(session, survey.survey_id)

    assert result.total == 45
    assert result.done == 40
    assert result.errors == 5
    assert result.finished is True
    assert result.estimated_seconds_left == 0


def test_empty_survey_has_no_progress_and_is_not_finished():
    from oceens import models  # noqa: F401
    from oceens.models import Survey

    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        survey = Survey()
        session.add(survey)
        session.commit()
        session.refresh(survey)

        from oceens.summary_progress import progress

        result = progress(session, survey.survey_id)

    assert result.total == 0
    assert result.done == 0
    assert result.errors == 0
    assert result.finished is False
    assert result.estimated_seconds_left == 0
