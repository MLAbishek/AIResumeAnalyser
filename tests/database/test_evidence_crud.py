from app.database.crud.jobs import create_job
from app.database.crud.resumes import create_resume
from app.database.crud.screening_results import (
    create_screening_result,
)
from app.database.crud.match_profiles import (
    create_match_profile,
)
from app.database.crud.evidence import (
    create_evidence_reference,
    delete_evidence_reference,
    get_evidence_reference,
    list_evidence_for_profile,
)


def create_test_profile(db):
    job = create_job(
        db,
        job_id="JOB-EVIDENCE-001",
        raw_text="Python developer",
    )

    resume = create_resume(
        db,
        resume_id="RESUME-EVIDENCE-001",
        raw_text="Python developer resume",
    )

    screening = create_screening_result(
        db,
        job_id=job.id,
        resume_id=resume.id,
        eligible=True,
        eligibility_details={},
    )

    return create_match_profile(
        db,
        screening_id=screening.id,
        gap_analysis={},
        explanation={},
    )


def test_create_and_get_evidence(db):
    profile = create_test_profile(db)

    evidence = create_evidence_reference(
        db,
        profile_id=profile.id,
        claim="Candidate has Python.",
        source="resume",
        section="skills",
        evidence="Python",
    )

    assert evidence.id is not None
    assert evidence.profile_id == profile.id

    fetched = get_evidence_reference(
        db,
        evidence.id,
    )

    assert fetched is not None
    assert fetched.id == evidence.id
    assert fetched.claim == "Candidate has Python."


def test_list_evidence_for_profile(db):
    profile = create_test_profile(db)

    create_evidence_reference(
        db,
        profile_id=profile.id,
        claim="Candidate has Python.",
        source="resume",
        section="skills",
        evidence="Python",
    )

    create_evidence_reference(
        db,
        profile_id=profile.id,
        claim="Candidate has FastAPI.",
        source="resume",
        section="skills",
        evidence="FastAPI",
    )

    references = list_evidence_for_profile(
        db,
        profile.id,
    )

    assert len(references) == 2

    claims = {
        reference.claim
        for reference in references
    }

    assert "Candidate has Python." in claims
    assert "Candidate has FastAPI." in claims


def test_delete_evidence(db):
    profile = create_test_profile(db)

    evidence = create_evidence_reference(
        db,
        profile_id=profile.id,
        claim="Candidate has Python.",
        source="resume",
        section="skills",
        evidence="Python",
    )

    evidence_id = evidence.id

    delete_evidence_reference(
        db,
        evidence,
    )

    assert get_evidence_reference(
        db,
        evidence_id,
    ) is None
def test_delete_match_profile_cascades_evidence(db):
    profile = create_test_profile(db)

    evidence = create_evidence_reference(
        db,
        profile_id=profile.id,
        claim="Candidate has Python.",
        source="resume",
        section="skills",
        evidence="Python",
    )

    evidence_id = evidence.id

    from app.database.crud.match_profiles import (
        delete_match_profile,
    )

    delete_match_profile(
        db,
        profile,
    )

    assert get_evidence_reference(
        db,
        evidence_id,
    ) is None