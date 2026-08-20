from sqlalchemy import select

from app.database.crud.jobs import create_job
from app.database.crud.resumes import create_resume
from app.database.crud.screening_results import (
    create_screening_result,
)
from app.database.models.ranking import RankingResult
from app.database.models.screening import ScreeningResult


def create_ranking_data(db):
    job = create_job(
        db,
        job_id="JOB-API-RANK-001",
        title="Python Developer",
        raw_text="Python developer with backend experience",
        required_skills=["python"],
        required_experience_months=24,
    )

    resume_1 = create_resume(
        db,
        resume_id="RESUME-API-RANK-001",
        name="Strong Candidate",
        skills=["python"],
        job_titles=["python developer"],
        total_experience_months=48,
        raw_text="Python developer with 4 years experience",
    )

    resume_2 = create_resume(
        db,
        resume_id="RESUME-API-RANK-002",
        name="Junior Candidate",
        skills=[],
        job_titles=["developer"],
        total_experience_months=12,
        raw_text="Junior developer",
    )

    screening_1 = create_screening_result(
        db,
        job_id=job.id,
        resume_id=resume_1.id,
        eligible=True,
        eligibility_details={},
    )

    screening_2 = create_screening_result(
        db,
        job_id=job.id,
        resume_id=resume_2.id,
        eligible=True,
        eligibility_details={},
    )

    db.flush()

    return (
        job,
        resume_1,
        resume_2,
        screening_1,
        screening_2,
    )


def test_ranking_endpoint_success(client, db):
    job, _, _, _, _ = create_ranking_data(db)

    response = client.post(
        f"/api/ranking/{job.job_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == job.job_id
    assert data["count"] == 2
    assert len(data["results"]) == 2

    assert data["results"][0]["rank"] == 1
    assert data["results"][1]["rank"] == 2

    assert (
        data["results"][0]["score"]
        >= data["results"][1]["score"]
    )


def test_ranking_endpoint_persists_results(client, db):
    job, _, _, screening_1, screening_2 = (
        create_ranking_data(db)
    )

    response = client.post(
        f"/api/ranking/{job.job_id}"
    )

    assert response.status_code == 200

    rankings = db.scalars(
        select(RankingResult)
        .where(
            RankingResult.screening_id.in_(
                [
                    screening_1.id,
                    screening_2.id,
                ]
            )
        )
        .order_by(RankingResult.rank)
    ).all()

    assert len(rankings) == 2
    assert rankings[0].rank == 1
    assert rankings[1].rank == 2


def test_ranking_endpoint_does_not_duplicate_results(
    client,
    db,
):
    job, _, _, screening_1, screening_2 = (
        create_ranking_data(db)
    )

    first_response = client.post(
        f"/api/ranking/{job.job_id}"
    )

    assert first_response.status_code == 200

    first_count = db.scalar(
        select(RankingResult)
        .where(
            RankingResult.screening_id == screening_1.id
        )
    )

    assert first_count is not None

    first_id = first_count.id

    second_response = client.post(
        f"/api/ranking/{job.job_id}"
    )

    assert second_response.status_code == 200

    rankings = db.scalars(
        select(RankingResult)
        .where(
            RankingResult.screening_id.in_(
                [
                    screening_1.id,
                    screening_2.id,
                ]
            )
        )
    ).all()

    assert len(rankings) == 2

    screening_1_rankings = [
        ranking
        for ranking in rankings
        if ranking.screening_id == screening_1.id
    ]

    assert len(screening_1_rankings) == 1
    assert screening_1_rankings[0].id == first_id


def test_ranking_endpoint_includes_ineligible_candidates(
    client,
    db,
):
    """
    Eligibility (hard gate) and ranking (relative strength) are
    separate concerns - an ineligible candidate can still have a
    real, evidence-backed score, and this endpoint must surface it
    the same way ScreeningService.screen() does, rather than
    silently dropping the candidate from the ranking table.
    """

    job = create_job(
        db,
        job_id="JOB-API-RANK-EMPTY",
        title="Python Developer",
        raw_text="Python developer",
    )

    resume = create_resume(
        db,
        resume_id="RESUME-API-RANK-INELIGIBLE",
        raw_text="Candidate",
    )

    create_screening_result(
        db,
        job_id=job.id,
        resume_id=resume.id,
        eligible=False,
        eligibility_details={
            "reason": "Does not meet requirements"
        },
    )

    db.flush()

    response = client.post(
        f"/api/ranking/{job.job_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == job.job_id
    assert data["count"] == 1
    assert len(data["results"]) == 1