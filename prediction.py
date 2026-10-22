
def assess_placement_readiness(data):
    """
    Calculate a student preparation score without depending
    on Gemini availability. Returns a numeric placement_level
    compatible with the existing PHP integration.
    """

    # 1. Read and validate student inputs
    try:
        cgpa = float(data.get("cgpa", 0))
        aptitude = float(data.get("aptitude", 0))
        projects = int(data.get("projects", 0))
        internships = int(data.get("internships", 0))
    except (TypeError, ValueError):
        raise ValueError(
            "Please enter valid numeric values for CGPA, aptitude, projects and internships."
        )

    skills = str(data.get("skills", "")).strip()
    target_role = str(data.get("target_role", "")).strip()

    if not 0 <= cgpa <= 10:
        raise ValueError("CGPA must be between 0 and 10.")

    if not 0 <= aptitude <= 100:
        raise ValueError("Aptitude score must be between 0 and 100.")

    if not 0 <= projects <= 30:
        raise ValueError("Project count must be between 0 and 30.")

    if not 0 <= internships <= 20:
        raise ValueError("Internship count must be between 0 and 20.")

    if not skills:
        raise ValueError("Please enter your skills.")

    # 2. Calculate preparation score out of 100
    skill_list = [
        skill.strip()
        for skill in skills.split(",")
        if skill.strip()
    ]

    cgpa_score = (cgpa / 10) * 30
    aptitude_score = (aptitude / 100) * 30
    project_score = (min(projects, 4) / 4) * 20
    internship_score = (min(internships, 2) / 2) * 10
    skill_score = (min(len(skill_list), 5) / 5) * 10

    placement_score = round(
        cgpa_score
        + aptitude_score
        + project_score
        + internship_score
        + skill_score,
        2
    )

    # 3. Determine preparation level
    if placement_score < 50:
        placement_level = 0
        placement_label = "Low Placement Readiness"
    elif placement_score < 75:
        placement_level = 1
        placement_label = "Medium Placement Readiness"
    else:
        placement_level = 2
        placement_label = "High Placement Readiness"

    # 4. Generate personalized feedback locally.
    # This does not require a Gemini API call.
    feedback = []

    feedback.append(
        f"Your preparation score is {placement_score}/100."
    )
    feedback.append(
        f"Your current preparation category is: {placement_label}."
    )

    feedback.append("\n1. Academic preparation")
    if cgpa < 6:
        feedback.append(
            "Focus on strengthening core subjects and improving your academic performance."
        )
    elif cgpa < 8:
        feedback.append(
            "Continue improving your academic performance and revise important core subjects."
        )
    else:
        feedback.append(
            "Your submitted CGPA is a positive academic indicator. Continue revising core subjects."
        )

    feedback.append("\n2. Aptitude preparation")
    if aptitude < 50:
        feedback.append(
            "Practise quantitative aptitude, logical reasoning and verbal ability regularly."
        )
    elif aptitude < 75:
        feedback.append(
            "Practise timed aptitude questions and review mistakes to improve accuracy."
        )
    else:
        feedback.append(
            "Maintain your aptitude performance with regular timed mock tests."
        )

    feedback.append("\n3. Skills and target role")
    feedback.append(
        "Skills provided: " + ", ".join(skill_list) + "."
    )
    feedback.append(
        "Target role: " + (target_role or "Not specified") + "."
    )
    feedback.append(
        "Compare your skills with current job descriptions for your target role and practise any missing requirements."
    )

    feedback.append("\n4. Projects and internships")
    if projects == 0:
        feedback.append(
            "Build a practical project related to your target role and publish the work in a portfolio."
        )
    elif projects < 3:
        feedback.append(
            "Improve your existing projects and build another project demonstrating practical problem-solving."
        )
    else:
        feedback.append(
            "Document your projects clearly, including your contribution, tools used and outcomes."
        )

    if internships == 0:
        feedback.append(
            "Look for relevant internships, practical training or supervised real-world projects."
        )
    else:
        feedback.append(
            "Prepare clear examples of your responsibilities and learning from your internship experience."
        )

    feedback.append("\n5. Interview preparation")
    feedback.append(
        "Practise explaining your projects, revise role-specific technical topics and conduct mock interviews."
    )

    feedback.append("\n6. Practical 30-day plan")
    feedback.append(
        "Week 1: Review aptitude and core technical concepts."
    )
    feedback.append(
        "Week 2: Improve one project and update your resume."
    )
    feedback.append(
        "Week 3: Practise technical and HR interview questions."
    )
    feedback.append(
        "Week 4: Take mock tests, review job descriptions and apply for suitable opportunities."
    )

    feedback.append(
        "\nImportant: This score measures preparation using the submitted information. "
        "It is not a hiring probability or a guarantee of placement. "
        "Actual selection depends on employer requirements, interviews and other factors."
    )

    return {
        "indicators": {
            "cgpa": cgpa,
            "aptitude_percentage": aptitude,
            "project_count": projects,
            "internship_count": internships,
            "listed_skills": skill_list,
            "placement_score": placement_score
        },
        "target_role": target_role,
        "placement_level": placement_level,
        "placement_label": placement_label,
        "ai_feedback": "\n".join(feedback)
    }
