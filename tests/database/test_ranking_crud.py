from app.database.crud.jobs import create_job
from app.database.crud.resumes import create_resume
from app.database.crud.screening_results import (
    create_screening_result,
)
from app.database.crud.ranking_results import (
    create_ranking_result,
    delete_ranking_result,
    get_ranking_by_screening_id,
    update_rank,
)


def create_screening(db):
    job = create_job(
        db,
        job_id="JOB-RANK-001",
        raw_text="Test job",
    )

    resume = create_resume(
        db,
        resume_id="RESUME-RANK-001",
        raw_text="Test resume",
    )

    return create_screening_result(
        db,
        job_id=job.id,
        resume_id=resume.id,
        eligible=True,
        eligibility_details={},
    )


def test_create_and_get_ranking(db):
    screening = create_screening(db)

    ranking = create_ranking_result(
        db,
        screening_id=screening.id,
        rank=1,
        score=0.92,
        skill_score=0.95,
        experience_score=0.90,
        seniority_score=0.88,
        education_score=0.90,
        semantic_score=0.94,
    )

    assert ranking.id is not None

    fetched = get_ranking_by_screening_id(
        db,
        screening.id,
    )

    assert fetched is not None
    assert fetched.score == 0.92
    assert fetched.skill_score == 0.95


def test_update_rank(db):
    screening = create_screening(db)

    ranking = create_ranking_result(
        db,
        screening_id=screening.id,
        rank=2,
        score=0.80,
        skill_score=0.80,
        experience_score=0.80,
        seniority_score=0.80,
        education_score=0.80,
        semantic_score=0.80,
    )

    updated = update_rank(
        db,
        ranking,
        rank=1,
    )

    assert updated.rank == 1


def test_delete_ranking(db):
    screening = create_screening(db)

    ranking = create_ranking_result(
        db,
        screening_id=screening.id,
        rank=1,
        score=0.90,
        skill_score=0.90,
        experience_score=0.90,
        seniority_score=0.90,
        education_score=0.90,
        semantic_score=0.90,
    )

    delete_ranking_result(
        db,
        ranking,
    )

    assert get_ranking_by_screening_id(
        db,
        screening.id,
    ) is None