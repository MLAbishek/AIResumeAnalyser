from app.filtering.schemas import (
    EligibilityCriteria,
    SkillMatchResult,
    ExperienceMatchResult,
    EducationCertificationResult,
    LocationAuthorizationResult,
    EligibilityResult,
)


def check_skills(
    candidate_skills,
    criteria: EligibilityCriteria
):
    matching = []
    missing = []

    candidate_skills_normalized = {
        skill.lower().strip()
        for skill in candidate_skills
    }

    reasons = []

    for skill in criteria.required_skills:
        if skill.lower().strip() in candidate_skills_normalized:
            matching.append(skill)
        else:
            missing.append(skill)

    eligible = len(missing) == 0

    if eligible:
        reasons.append("All skills satisfied")
    else:
        reasons.append(
            f"Missing required skills: {', '.join(missing)}"
        )

    return SkillMatchResult(
        matched_skills=matching,
        missing_skills=missing,
        eligible=eligible,
        reasons=reasons,
    )


def check_experience(
    candidate_experience_months,
    criteria: EligibilityCriteria
):
    required_months = criteria.minimum_experience_months
    candidate_months = candidate_experience_months

    eligible = candidate_months >= required_months

    reasons = []

    if eligible:
        reasons.append(
            "Candidate satisfies the required experience."
        )
    else:
        reasons.append(
            f"Candidate has {candidate_months} months of experience, "
            f"but {required_months} months are required."
        )

    return ExperienceMatchResult(
        required_months=required_months,
        candidate_months=candidate_months,
        relevant_months=candidate_months,
        seniority_match=None,
        eligible=eligible,
        reasons=reasons,
    )


def check_education_certification(
    candidate_education,
    candidate_certifications,
    criteria: EligibilityCriteria
):
    education_match = True
    certification_match = True

    reasons = []

    if criteria.required_education:
        education_match = False

        candidate_education_normalized = (
            candidate_education.lower().strip()
        )

        for requirement in criteria.required_education:
            degree_match = True
            field_match = True

            if requirement.degree:
                degree_match = (
                    requirement.degree.lower().strip()
                    in candidate_education_normalized
                )

            if requirement.field_of_study:
                field_match = (
                    requirement.field_of_study.lower().strip()
                    in candidate_education_normalized
                )

            if degree_match and field_match:
                education_match = True
                break

        if education_match:
            reasons.append(
                "Education requirement satisfied."
            )
        else:
            reasons.append(
                "Required education not found."
            )

    if criteria.required_certifications:
        candidate_certifications_normalized = {
            certification.lower().strip()
            for certification in candidate_certifications
        }

        missing_certifications = []

        for certification in criteria.required_certifications:
            if (
                certification.lower().strip()
                not in candidate_certifications_normalized
            ):
                missing_certifications.append(certification)

        certification_match = (
            len(missing_certifications) == 0
        )

        if certification_match:
            reasons.append(
                "Certification requirements satisfied."
            )
        else:
            reasons.append(
                f"Missing certifications: "
                f"{', '.join(missing_certifications)}"
            )

    eligible = education_match and certification_match

    return EducationCertificationResult(
        eligible=eligible,
        reasons=reasons,
    )


def check_location(
    candidate_location,
    criteria: EligibilityCriteria,
):
    required_location = criteria.location

    if not required_location:
        return True, "No location requirement specified."

    if not candidate_location:
        return (
            False,
            "Candidate location is unavailable.",
        )

    location_match = (
        candidate_location.lower().strip()
        == required_location.lower().strip()
    )

    if location_match:
        reason = "Location requirement satisfied."
    else:
        reason = (
            f"Candidate location '{candidate_location}' "
            f"does not match required location "
            f"'{required_location}'."
        )

    return location_match, reason


def check_location_authorization(
    candidate_location,
    candidate_authorization,
    criteria: EligibilityCriteria
):
    location_match, location_reason = check_location(
        candidate_location,
        criteria
    )

    authorization_match = True

    reasons = [
        location_reason
    ]

    if criteria.work_authorization_required:
        authorization_match = candidate_authorization

        if authorization_match:
            reasons.append(
                "Authorization requirement satisfied."
            )
        else:
            reasons.append(
                "Candidate does not satisfy "
                "the authorization requirement."
            )

    eligible = (
        location_match
        and authorization_match
    )

    return LocationAuthorizationResult(
        location_match=location_match,
        authorization_match=authorization_match,
        eligible=eligible,
        reasons=reasons,
    )


def check_eligibility(
    candidate,
    criteria: EligibilityCriteria
):
    skill_result = check_skills(
        candidate.skills,
        criteria
    )

    experience_result = check_experience(
        candidate.experience_months,
        criteria
    )

    education_result = check_education_certification(
        candidate.education,
        candidate.certifications,
        criteria
    )

    location_result = check_location_authorization(
        candidate.location,
        candidate.authorization,
        criteria
    )

    eligible = (
        skill_result.eligible
        and experience_result.eligible
        and education_result.eligible
        and location_result.eligible
    )

    reasons = (
        skill_result.reasons
        + experience_result.reasons
        + education_result.reasons
        + location_result.reasons
    )

    return EligibilityResult(
        eligible=eligible,
        skill_match=skill_result,
        experience_match=experience_result,
        education_certification=education_result,
        location_authorization=location_result,
        reasons=reasons,
    )