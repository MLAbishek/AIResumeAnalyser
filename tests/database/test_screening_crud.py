from app.database.crud.jobs import create_job
from app.database.crud.resumes import create_resume
from app.database.crud.screening_results import (
    create_screening_result,
    delete_screening_result,
    get_screening_by_id,
    get_screening_result,
    list_screening_results_for_job,
    update_screening_result,
)


def create_test_job(db, job_id="JOB-SCREEN-001"):
    return create_job(
        db,
        job_id=job_id,
        raw_text="Test job",
    )


def create_test_resume(db, resume_id="RESUME-SCREEN-001"):
    return create_resume(
        db,
        resume_id=resume_id,
        raw_text="Test resume",
    )


def test_create_screening_result(db):
    job = create_test_job(db)
    resume = create_test_resume(db)

    result = create_screening_result(
        db,
        job_id=job.id,
        resume_id=resume.id,
        eligible=True,
        eligibility_details={
            "skills": "passed",
            "experience": "passed",
        },
        decision="shortlist",
        final_score=87.5,
        decision_reason="Strong candidate",
    )

    assert result.id is not None
    assert result.eligible is True
    assert result.final_score == 87.5


def test_get_screening_result(db):
    job = create_test_job(db)
    resume = create_test_resume(db)

    created = create_screening_result(
        db,
        job_id=job.id,
        resume_id=resume.id,
        eligible=True,
        eligibility_details={},
    )

    fetched = get_screening_result(
        db,
        job_id=job.id,
        resume_id=resume.id,
    )

    assert fetched is not None
    assert fetched.id == created.id


def test_get_screening_by_id(db):
    job = create_test_job(db)
    resume = create_test_resume(db)

    created = create_screening_result(
        db,
        job_id=job.id,
        resume_id=resume.id,
        eligible=True,
        eligibility_details={},
    )

    fetched = get_screening_by_id(
        db,
        created.id,
    )

    assert fetched is not None
    assert fetched.id == created.id


def test_update_screening_result(db):
    job = create_test_job(db)
    resume = create_test_resume(db)

    result = create_screening_result(
        db,
        job_id=job.id,
        resume_id=resume.id,
        eligible=True,
        eligibility_details={},
    )

    updated = update_screening_result(
        db,
        result,
        decision="shortlist",
        final_score=92.0,
        decision_reason="Excellent match",
    )

    assert updated.decision == "shortlist"
    assert updated.final_score == 92.0


def test_list_screening_results_for_job(db):
    job = create_test_job(db)

    resume1 = create_test_resume(
        db,
        "RESUME-SCREEN-002",
    )

    resume2 = create_test_resume(
        db,
        "RESUME-SCREEN-003",
    )

    create_screening_result(
        db,
        job_id=job.id,
        resume_id=resume1.id,
        eligible=True,
        eligibility_details={},
        final_score=70,
    )

    create_screening_result(
        db,
        job_id=job.id,
        resume_id=resume2.id,
        eligible=True,
        eligibility_details={},
        final_score=90,
    )

    results = list_screening_results_for_job(
        db,
        job.id,
    )

    assert len(results) == 2
    assert results[0].final_score == 90
    assert results[1].final_score == 70


def test_delete_screening_result(db):
    job = create_test_job(db)
    resume = create_test_resume(db)

    result = create_screening_result(
        db,
        job_id=job.id,
        resume_id=resume.id,
        eligible=True,
        eligibility_details={},
    )

    delete_screening_result(
        db,
        result,
    )

    assert get_screening_by_id(
        db,
        result.id,
    ) is None

def test_delete_screening_cascades_related_records(db):
    from app.database.crud.ranking_results import (
        create_ranking_result,
        get_ranking_by_screening_id,
    )

    from app.database.crud.match_profiles import (
        create_match_profile,
        get_match_profile,
    )

    from app.database.crud.evidence import (
        create_evidence_reference,
        get_evidence_reference,
    )

    job = create_test_job(
        db,
        "JOB-CASCADE-001",
    )

    resume = create_test_resume(
        db,
        "RESUME-CASCADE-001",
    )

    screening = create_screening_result(
        db,
        job_id=job.id,
        resume_id=resume.id,
        eligible=True,
        eligibility_details={},
    )

    ranking = create_ranking_result(
        db,
        screening_id=screening.id,
        rank=1,
        score=0.95,
        skill_score=0.95,
        experience_score=0.90,
        seniority_score=0.90,
        education_score=0.90,
        semantic_score=0.95,
    )

    profile = create_match_profile(
        db,
        screening_id=screening.id,
        gap_analysis={},
        explanation={},
    )

    evidence = create_evidence_reference(
        db,
        profile_id=profile.id,
        claim="Candidate has Python.",
        source="resume",
        section="skills",
        evidence="Python",
    )

    ranking_id = ranking.id
    profile_id = profile.id
    evidence_id = evidence.id

    delete_screening_result(
        db,
        screening,
    )

    assert get_screening_by_id(
        db,
        screening.id,
    ) is None

    assert get_ranking_by_screening_id(
        db,
        screening.id,
    ) is None

    assert get_match_profile(
        db,
        screening.id,
    ) is None

    assert get_evidence_reference(
        db,
        evidence_id,
    ) is None