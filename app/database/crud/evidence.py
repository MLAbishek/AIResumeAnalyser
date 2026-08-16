from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.evidence import EvidenceReference


def create_evidence_reference(
    db: Session,
    *,
    profile_id: int,
    claim: str,
    source: str,
    section: str,
    evidence: str,
) -> EvidenceReference:
    reference = EvidenceReference(
        profile_id=profile_id,
        claim=claim,
        source=source,
        section=section,
        evidence=evidence,
    )

    db.add(reference)
    db.commit()
    db.refresh(reference)

    return reference


def get_evidence_reference(
    db: Session,
    evidence_id: int,
) -> EvidenceReference | None:
    return db.get(
        EvidenceReference,
        evidence_id,
    )


def list_evidence_for_profile(
    db: Session,
    profile_id: int,
) -> list[EvidenceReference]:
    statement = (
        select(EvidenceReference)
        .where(
            EvidenceReference.profile_id == profile_id
        )
        .order_by(EvidenceReference.id)
    )

    return list(db.scalars(statement).all())


def delete_evidence_reference(
    db: Session,
    reference: EvidenceReference,
) -> None:
    db.delete(reference)
    db.commit()