from typing import Any

from sqlalchemy.orm import Session

from app.database.crud.evidence import (
    create_evidence_reference,
)
from app.database.crud.jobs import get_job_by_id
from app.database.crud.match_profiles import (
    create_match_profile,
)
from app.database.crud.ranking_results import (
    create_ranking_result,
)
from app.database.crud.resumes import get_resume_by_id
from app.database.crud.screening_results import (
    create_screening_result,
)


class ScreeningPersistenceService:
    """
    Persists complete screening results into the database.

    One screening request is handled as one database
    transaction. If any part fails, the entire operation
    is rolled back.
    """

    def __init__(self, db: Session):
        self.db = db

    def persist(
        self,
        *,
        job_id: str,
        results: list[dict[str, Any]],
    ) -> list[int]:
        job = get_job_by_id(
            self.db,
            job_id,
        )

        if job is None:
            raise ValueError(
                f"Job '{job_id}' not found."
            )

        screening_ids: list[int] = []

        try:
            for result in results:
                resume_id = result["resume_id"]

                resume = get_resume_by_id(
                    self.db,
                    resume_id,
                )

                if resume is None:
                    raise ValueError(
                        f"Resume '{resume_id}' not found."
                    )

                screening = create_screening_result(
                    self.db,
                    job_id=job.id,
                    resume_id=resume.id,
                    eligible=result["eligible"],
                    eligibility_details=(
                        result["eligibility"]
                    ),
                    decision=result["decision"],
                    final_score=result[
                        "ranking_score_percent"
                    ],
                    decision_reason=result[
                        "decision_reason"
                    ],
                )

                screening_ids.append(
                    screening.id
                )

                self._persist_ranking(
                    screening_id=screening.id,
                    ranking=result.get("ranking"),
                )

                profile = create_match_profile(
                    self.db,
                    screening_id=screening.id,
                    gap_analysis=result[
                        "gap_analysis"
                    ],
                    explanation=result[
                        "explanation"
                    ],
                )

                self._persist_evidence(
                    profile_id=profile.id,
                    evidence=result.get(
                        "evidence",
                        [],
                    ),
                )

            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        return screening_ids

    def _persist_ranking(
        self,
        *,
        screening_id: int,
        ranking: dict[str, Any] | None,
    ) -> None:
        if ranking is None:
            return

        features = ranking.get(
            "features",
            {},
        )

        create_ranking_result(
            self.db,
            screening_id=screening_id,
            rank=ranking.get("rank"),
            score=float(
                ranking.get("score", 0.0)
            ),
            skill_score=float(
                features.get(
                    "skill_score",
                    0.0,
                )
            ),
            experience_score=float(
                features.get(
                    "experience_score",
                    0.0,
                )
            ),
            seniority_score=float(
                features.get(
                    "seniority_score",
                    0.0,
                )
            ),
            education_score=float(
                features.get(
                    "education_score",
                    0.0,
                )
            ),
            semantic_score=float(
                features.get(
                    "semantic_score",
                    0.0,
                )
            ),
        )

    def _persist_evidence(
        self,
        *,
        profile_id: int,
        evidence: list[dict[str, Any]],
    ) -> None:
        for reference in evidence:
            create_evidence_reference(
                self.db,
                profile_id=profile_id,
                claim=str(
                    reference.get(
                        "claim",
                        "",
                    )
                ),
                source=str(
                    reference.get(
                        "source",
                        "",
                    )
                ),
                section=str(
                    reference.get(
                        "section",
                        "",
                    )
                ),
                evidence=str(
                    reference.get(
                        "evidence",
                        "",
                    )
                ),
            )