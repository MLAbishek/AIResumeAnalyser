import pytest

from app.reporting import (
    ScreeningReportGenerator,
)


def _candidate(
    *,
    resume_id="RES_001",
    decision="shortlist",
    eligible=True,
    score=87.5,
):
    return {
        "resume_id": resume_id,
        "eligible": eligible,
        "ranking_score": score / 100,
        "ranking_score_percent": score,
        "decision": decision,
        "decision_reason": "Strong overall match.",
        "eligibility": {
            "experience_match": {
                "eligible": True
            }
        },
        "gap_analysis": {
            "matched_skills": [
                "python",
                "machine learning",
            ],
            "missing_skills": [
                "kubernetes"
            ],
        },
        "explanation": {
            "summary": (
                "Candidate is shortlisted."
            ),
            "strengths": [
                "Matched required skills: python, machine learning."
            ],
            "gaps": [
                "Missing required skills: kubernetes."
            ],
        },
        "evidence": [
            {
                "claim": "Python experience",
                "source": "resume",
                "section": "skills",
                "evidence": "Python",
            }
        ],
    }


def test_generate_report():

    evaluation = {
        "job_id": "JD_001",
        "total_candidates": 1,
        "eligible_candidates": 1,
        "results": [
            _candidate()
        ],
    }

    report = ScreeningReportGenerator().generate(
        evaluation
    )

    assert report.job_id == "JD_001"
    assert report.total_candidates == 1
    assert report.eligible_candidates == 1
    assert report.shortlisted_candidates == 1
    assert report.review_candidates == 0
    assert report.rejected_candidates == 0

    assert len(report.candidates) == 1

    candidate = report.candidates[0]

    assert candidate.resume_id == "RES_001"
    assert candidate.decision == "shortlist"
    assert candidate.eligible is True
    assert candidate.ranking_score == 87.5

    assert "python" in candidate.matched_skills
    assert "kubernetes" in candidate.missing_skills


def test_report_contains_markdown():

    evaluation = {
        "job_id": "JD_001",
        "results": [
            _candidate()
        ],
    }

    report = ScreeningReportGenerator().generate(
        evaluation
    )

    assert "# Screening Report — JD_001" in report.markdown
    assert "## Summary" in report.markdown
    assert "## Candidate Results" in report.markdown
    assert "RES_001" in report.markdown
    assert "87.50/100" in report.markdown


def test_multiple_decisions_are_counted():

    evaluation = {
        "job_id": "JD_002",
        "results": [
            _candidate(
                resume_id="RES_001",
                decision="shortlist",
                eligible=True,
                score=90,
            ),
            _candidate(
                resume_id="RES_002",
                decision="review",
                eligible=True,
                score=65,
            ),
            _candidate(
                resume_id="RES_003",
                decision="reject",
                eligible=False,
                score=20,
            ),
        ],
    }

    report = ScreeningReportGenerator().generate(
        evaluation
    )

    assert report.total_candidates == 3
    assert report.eligible_candidates == 2
    assert report.shortlisted_candidates == 1
    assert report.review_candidates == 1
    assert report.rejected_candidates == 1


def test_empty_results_generate_valid_report():

    evaluation = {
        "job_id": "JD_EMPTY",
        "results": [],
    }

    report = ScreeningReportGenerator().generate(
        evaluation
    )

    assert report.total_candidates == 0
    assert report.eligible_candidates == 0
    assert report.candidates == []

    assert (
        "No candidates were supplied"
        in report.markdown
    )


def test_invalid_evaluation_type_is_rejected():

    with pytest.raises(TypeError):

        ScreeningReportGenerator().generate(
            []
        )


def test_missing_job_id_is_rejected():

    with pytest.raises(ValueError):

        ScreeningReportGenerator().generate(
            {
                "results": []
            }
        )


def test_missing_results_is_rejected():

    with pytest.raises(ValueError):

        ScreeningReportGenerator().generate(
            {
                "job_id": "JD_001"
            }
        )


def test_invalid_decision_is_rejected():

    evaluation = {
        "job_id": "JD_001",
        "results": [
            _candidate(
                decision="unknown"
            )
        ],
    }

    with pytest.raises(ValueError):

        ScreeningReportGenerator().generate(
            evaluation
        )


def test_missing_optional_evaluation_sections_are_handled():

    evaluation = {
        "job_id": "JD_001",
        "results": [
            {
                "resume_id": "RES_001",
                "eligible": False,
                "decision": "reject",
                "decision_reason": "Not eligible.",
                "ranking_score_percent": None,
            }
        ],
    }

    report = ScreeningReportGenerator().generate(
        evaluation
    )

    candidate = report.candidates[0]

    assert candidate.resume_id == "RES_001"
    assert candidate.ranking_score == 0.0
    assert candidate.strengths == []
    assert candidate.gaps == []
    assert candidate.matched_skills == []
    assert candidate.missing_skills == []
    assert candidate.evidence == []