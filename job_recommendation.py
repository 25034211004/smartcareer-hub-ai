
def parse_skills(value):
    if isinstance(value, list):
        parts = value
    elif isinstance(value, str):
        parts = value.split(",")
    else:
        parts = []

    return {
        str(skill).strip().lower()
        for skill in parts
        if str(skill).strip()
    }


def recommend_jobs(student_skills, preferred_role, jobs):
    skills = parse_skills(student_skills)

    if not skills:
        raise ValueError("Please enter your skills.")

    if not isinstance(jobs, list):
        raise ValueError("Invalid jobs list.")

    preferred_role = str(preferred_role or "").strip()
    recommendations = []

    for job in jobs:
        if not isinstance(job, dict):
            continue

        required = parse_skills(job.get("required_skills", ""))
        matched = sorted(skills & required)
        missing = sorted(required - skills)

        percentage = (
            round(len(matched) / len(required) * 100)
            if required else 0
        )

        title = str(job.get("job_title") or "")
        company = str(job.get("company") or "")
        location = str(job.get("location") or "")

        role_match = (
            preferred_role.lower() in title.lower()
            if preferred_role else False
        )

        recommendations.append({
            "job_id": job.get("id"),
            "job_title": title,
            "company": company,
            "location": location,
            "required_skills": sorted(required),
            "matched_skills": matched,
            "missing_skills": missing,
            "skill_coverage": percentage,
            "role_match": role_match,
            "ai_feedback": (
                f"This role matches {len(matched)} of "
                f"{len(required)} listed required skills. "
                + (
                    "Consider learning: " + ", ".join(missing) + "."
                    if missing
                    else "Continue practising and preparing for interviews."
                )
            )
        })

    recommendations.sort(
        key=lambda item: (
            item["role_match"],
            item["skill_coverage"],
            item["job_title"].lower()
        ),
        reverse=True
    )

    top_jobs = [
        job for job in recommendations
        if job["matched_skills"] or job["role_match"]
    ][:5]

    return top_jobs
