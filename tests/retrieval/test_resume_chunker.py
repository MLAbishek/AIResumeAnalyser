from datetime import date

from app.core.schemas import (
    CanonicalEducation,
    CanonicalExperience,
    CanonicalResume,
)
from app.retrieval.resume_chunker import ResumeChunker


def make_resume(
    resume_id: str = "resume-1",
) -> CanonicalResume:
    return CanonicalResume(
        resume_id=resume_id,
        name="Alice",
        summary="Machine learning engineer with Python experience.",
        skills=["Python", "Machine Learning"],
        job_titles=["ML Engineer"],
        organizations=["ABC Corp"],
        technologies=["TensorFlow", "PyTorch"],
        experiences=[
            CanonicalExperience(
                job_title="ML Engineer",
                company="ABC Corp",
                start_date=date(2022, 1, 1),
                end_date=date(2024, 1, 1),
                duration_months=24,
            ),
            CanonicalExperience(
                job_title="Software Engineer",
                company="XYZ Ltd",
                start_date=date(2020, 1, 1),
                end_date=date(2022, 1, 1),
                duration_months=24,
            ),
        ],
        education=[
            CanonicalEducation(
                degree="B.Tech",
                institution="ABC University",
                field_of_study="Computer Science",
                start_date=date(2016, 1, 1),
                end_date=date(2020, 1, 1),
            )
        ],
        total_experience_months=48,
    )


def test_chunk_resume_creates_semantic_sections():
    resume = make_resume()

    chunks = ResumeChunker().chunk(resume)

    sections = [chunk.section for chunk in chunks]

    assert sections == [
        "summary",
        "skills",
        "job_titles",
        "organizations",
        "technologies",
        "experience",
        "experience",
        "education",
    ]


def test_chunk_preserves_resume_id():
    resume = make_resume()

    chunks = ResumeChunker().chunk(resume)

    assert all(chunk.resume_id == "resume-1" for chunk in chunks)


def test_chunk_preserves_experience_metadata():
    resume = make_resume()

    chunks = ResumeChunker().chunk(resume)

    experience_chunks = [
        chunk for chunk in chunks
        if chunk.section == "experience"
    ]

    assert len(experience_chunks) == 2

    first = experience_chunks[0]

    assert first.metadata["experience_index"] == 0
    assert first.metadata["job_title"] == "ML Engineer"
    assert first.metadata["company"] == "ABC Corp"
    assert first.metadata["duration_months"] == 24


def test_chunk_preserves_education_metadata():
    resume = make_resume()

    chunks = ResumeChunker().chunk(resume)

    education_chunks = [
        chunk for chunk in chunks
        if chunk.section == "education"
    ]

    assert len(education_chunks) == 1

    chunk = education_chunks[0]

    assert chunk.metadata["degree"] == "B.Tech"
    assert chunk.metadata["institution"] == "ABC University"
    assert chunk.metadata["field_of_study"] == "Computer Science"


def test_empty_sections_are_not_created():
    resume = CanonicalResume(
        resume_id="resume-empty",
    )

    chunks = ResumeChunker().chunk(resume)

    assert chunks == []


def test_whitespace_summary_is_ignored():
    resume = CanonicalResume(
        resume_id="resume-1",
        summary="   ",
        skills=["Python"],
    )

    chunks = ResumeChunker().chunk(resume)

    assert len(chunks) == 1
    assert chunks[0].section == "skills"


def test_chunk_ids_are_deterministic():
    resume = make_resume()

    chunker = ResumeChunker()

    first = chunker.chunk(resume)
    second = chunker.chunk(resume)

    assert [chunk.chunk_id for chunk in first] == [
        chunk.chunk_id for chunk in second
    ]


def test_chunk_ids_are_unique():
    resume = make_resume()

    chunks = ResumeChunker().chunk(resume)

    ids = [chunk.chunk_id for chunk in chunks]

    assert len(ids) == len(set(ids))


def test_chunk_positions_are_sequential():
    resume = make_resume()

    chunks = ResumeChunker().chunk(resume)

    assert [chunk.position for chunk in chunks] == list(
        range(len(chunks))
    )


def test_chunk_many_preserves_candidate_identity():
    resume_1 = make_resume("resume-1")
    resume_2 = make_resume("resume-2")

    chunks = ResumeChunker().chunk_many(
        [resume_1, resume_2]
    )

    resume_ids = {chunk.resume_id for chunk in chunks}

    assert resume_ids == {"resume-1", "resume-2"}

    assert sum(
        chunk.resume_id == "resume-1"
        for chunk in chunks
    ) == 8

    assert sum(
        chunk.resume_id == "resume-2"
        for chunk in chunks
    ) == 8


def test_experience_text_contains_retrievable_terms():
    resume = make_resume()

    chunks = ResumeChunker().chunk(resume)

    experience = next(
        chunk
        for chunk in chunks
        if chunk.section == "experience"
    )

    assert "ML Engineer" in experience.text
    assert "ABC Corp" in experience.text
    assert "24 months" in experience.text