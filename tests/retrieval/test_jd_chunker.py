from app.core.schemas import (
    CanonicalJob,
    CanonicalJobEducationRequirement,
    CanonicalJobExperienceRequirement,
)
from app.retrieval.jd_chunker import JDChunker


def make_job(**overrides) -> CanonicalJob:
    defaults = dict(
        job_id="job-1",
        title="Frontend Developer Intern",
        description="Build responsive web applications.",
        required_skills=["html", "css", "javascript"],
        preferred_skills=["react", "typescript"],
        required_technologies=["git"],
        preferred_technologies=["vite"],
        responsibilities=[
            "Build responsive and interactive web interfaces.",
            "Integrate frontend applications with REST APIs.",
        ],
        education=[
            CanonicalJobEducationRequirement(
                degree="bachelor",
                field_of_study="computer science",
            )
        ],
    )
    defaults.update(overrides)
    return CanonicalJob(**defaults)


def test_chunks_have_expected_sections():
    chunker = JDChunker()

    chunks = chunker.chunk(make_job())

    sections = {chunk.section for chunk in chunks}

    assert "description" in sections
    assert "responsibilities" in sections
    assert "required_skills" in sections
    assert "preferred_skills" in sections
    assert "technologies" in sections
    assert "education" in sections


def test_responsibilities_are_preserved_verbatim():
    chunker = JDChunker()

    chunks = chunker.chunk(make_job())

    responsibilities_chunk = next(
        chunk
        for chunk in chunks
        if chunk.section == "responsibilities"
    )

    assert (
        "Build responsive and interactive web interfaces."
        in responsibilities_chunk.text
    )
    assert (
        "Integrate frontend applications with REST APIs."
        in responsibilities_chunk.text
    )


def test_chunk_ids_are_deterministic():
    chunker = JDChunker()
    job = make_job()

    first = chunker.chunk(job)
    second = chunker.chunk(job)

    assert [c.chunk_id for c in first] == [
        c.chunk_id for c in second
    ]


def test_chunk_ids_are_unique():
    chunker = JDChunker()

    chunks = chunker.chunk(make_job())

    ids = [chunk.chunk_id for chunk in chunks]

    assert len(ids) == len(set(ids))


def test_all_chunks_carry_job_id():
    chunker = JDChunker()

    chunks = chunker.chunk(make_job(job_id="job-42"))

    assert all(chunk.job_id == "job-42" for chunk in chunks)


def test_empty_sections_produce_no_chunk():
    chunker = JDChunker()

    job = CanonicalJob(
        job_id="job-empty",
        experience=CanonicalJobExperienceRequirement(),
    )

    chunks = chunker.chunk(job)

    assert chunks == []


def test_positions_are_sequential():
    chunker = JDChunker()

    chunks = chunker.chunk(make_job())

    assert [chunk.position for chunk in chunks] == list(
        range(len(chunks))
    )
