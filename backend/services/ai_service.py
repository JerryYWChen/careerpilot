import os

from dotenv import load_dotenv
from openai import OpenAI
from backend.models.analysis import Gap, JobRequirements, ResumeMatchResult, MatchAnalysis, ResumeHighlights, RecommendationReview, CareerActionPlan

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def analyze_job_description(job_description: str) -> JobRequirements:
    response = client.responses.parse(
        model="gpt-5.6-luna",
        input=[
            {
                "role": "system",
                "content": (
                    "Analyze the job description and extract its requirements. "
                    "Only extract requirements that are explicitly stated or "
                    "clearly supported by the job description. "
                    "Do not invent requirements. "
                    "If seniority is unclear, use unknown. "
                    "Only provide minimum years when the job description "
                    "explicitly states a number of years."
                ),
            },
            {
                "role": "user",
                "content": job_description,
            },
        ],
        text_format=JobRequirements,
    )

    return response.output_parsed

def match_resume_to_requirements(
    resume_text: str,
    job_requirements: JobRequirements
) -> ResumeMatchResult:
    response = client.responses.parse(
        model="gpt-5.6-luna",
        input=[
            {
                "role": "system",
                "content": (
                    "Evaluate the resume against every provided job requirement. "
                    "Return exactly one match result for every requirement. "

                    "Use only information and evidence contained in the resume. "
                    "Do not invent, assume, or exaggerate the candidate's skills, experience, "
                    "achievements, or qualifications. "

                    "Evaluate the total strength of the evidence for each requirement. "
                    "Evidence may come from skills, work experience, projects, research, "
                    "education, certifications, technologies, frameworks, libraries, or "
                    "implementation details. Consider multiple pieces of related evidence "
                    "together rather than evaluating each piece in isolation. "

                    "Classify a requirement as 'matched' when the resume provides either direct "
                    "evidence or strong contextual evidence that reliably demonstrates the "
                    "requirement. Strong contextual evidence can come from a combination of "
                    "related technologies, frameworks, libraries, and concrete implementation "
                    "work, even when the exact requirement keyword is not explicitly stated. "

                    "Classify a requirement as 'partial' when relevant evidence exists but is "
                    "weak, incomplete, indirect, or insufficient to reliably establish the "
                    "requirement. A skill that is only listed in the Skills section without "
                    "supporting contextual or practical evidence should normally be classified "
                    "as 'partial'. "

                    "Classify a requirement as 'missing' when the resume provides no reasonable "
                    "evidence supporting the requirement. Do not infer a requirement merely from "
                    "a broadly related field, coursework, or a single weakly related technology. "

                    "For requirements that specify a minimum number of years, compare the resume "
                    "evidence with the required number of years. If relevant experience exists "
                    "but the minimum number of years is not satisfied or cannot be clearly "
                    "established, classify the requirement as 'partial'. "

                    "Provide evidence from the resume whenever evidence exists. "
                    "Explain why the evidence supports the classification. "
                    "When relying on contextual evidence, explain how the combination of evidence "
                    "reliably supports the requirement."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Resume:\n{resume_text}\n\n"
                    f"Job requirements:\n"
                    f"{job_requirements.model_dump_json()}"
                ),
            },
        ],
        text_format=ResumeMatchResult,
    )

    return response.output_parsed

def generate_resume_highlights(
    resume_text: str,
    job_requirements: JobRequirements,
    match_analysis: MatchAnalysis,
) -> ResumeHighlights:

    response = client.responses.parse(
        model="gpt-5.6-luna",
        input=[
            {
                "role": "system",
                "content": (
                    "You are a resume presentation advisor. "
                    "Recommend how the candidate can better highlight "
                    "existing strengths that are already supported by the resume. "

                    "Focus only on matched requirements and existing evidence. "
                    "Suggest clearer positioning, wording, organization, or emphasis. "

                    "Do not recommend learning missing skills or building new projects. "
                    "Do not provide gap-closing actions. "
                    "Do not invent or exaggerate skills, experience, metrics, "
                    "achievements, or qualifications. "

                    "Every recommendation must be grounded in evidence already "
                    "present in the resume."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Resume:\n{resume_text}\n\n"
                    f"Job requirements:\n"
                    f"{job_requirements.model_dump_json()}\n\n"
                    f"Matched strengths:\n"
                    f"{[strength.model_dump() for strength in match_analysis.strengths]}"
                ),
            },
        ],
        text_format=ResumeHighlights,
    )

    return response.output_parsed

def generate_resume_improvement(gap: Gap, review_feedback: str | None = None) -> str:
    prompt = f"""
You are a resume improvement coach.

The candidate has a partially matched job requirement.

Requirement:
{gap.area}

Existing resume evidence:
{gap.evidence or "No specific evidence provided."}

Reason for partial match:
{gap.reason}

Your task:
- Give one specific and actionable recommendation for improving how this existing evidence is presented on the resume.
- Focus on clarifying, reorganizing, or strengthening existing evidence.
- Do not invent skills, experience, projects, metrics, or achievements.
- If the existing evidence is not sufficient to support a stronger claim, say what additional real evidence the candidate would need before making that claim.
- Keep the recommendation concise.

Return only the recommendation.
"""
    if review_feedback:
        prompt += f"""

A previous recommendation did not pass review.

Reviewer feedback:
{review_feedback}

Generate an improved recommendation that specifically addresses
the reviewer feedback.
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=prompt,
    )

    return response.output_text.strip()

def generate_skill_development(
    gap: Gap,
    review_feedback: str | None = None
) -> str:
    prompt = f"""
You are a career skill development coach.

The candidate is missing a job requirement.

Requirement:
{gap.area}

Reason it is considered missing:
{gap.reason}

Your task:
- Give one specific and actionable way for the candidate to build real evidence for this missing requirement.
- Prefer a small hands-on project when practical.
- Explain what the candidate should build, practice, or learn.
- Do not assume the candidate already has experience with the missing skill.
- Do not invent experience, achievements, or qualifications.
- Keep the recommendation concise and realistic.

Return only the recommendation.
"""

    if review_feedback:
        prompt += f"""

A previous recommendation did not pass review.

Reviewer feedback:
{review_feedback}

Generate an improved recommendation that specifically addresses
the reviewer feedback.
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=prompt,
    )

    return response.output_text.strip()

def review_recommendation(
    gap: Gap,
    recommendation: str
) -> RecommendationReview:

    response = client.responses.parse(
        model="gpt-5.6-luna",
        input=[
            {
                "role": "system",
                "content": (
                    "You are reviewing a career recommendation. "
                    "Evaluate whether it is grounded and actionable. "
                    "It must not invent or assume candidate experience, "
                    "skills, projects, achievements, or qualifications. "
                    "It must provide a specific action rather than vague advice. "
                    "If it fails, explain specifically what should be improved. "
                    "If it passes, briefly explain why."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Requirement: {gap.area}\n"
                    f"Gap status: {gap.status.value}\n"
                    f"Existing evidence: "
                    f"{gap.evidence or 'No specific evidence provided.'}\n"
                    f"Reason for gap: {gap.reason}\n\n"
                    f"Recommendation:\n{recommendation}"
                ),
            },
        ],
        text_format=RecommendationReview,
    )

    return response.output_parsed

def generate_career_action_plan(
    gaps: list[Gap],
    validation_feedback: str | None = None,
) -> CareerActionPlan:

    gap_text = "\n".join(
        f"- {gap.area} | status={gap.status.value} | "
        f"evidence={gap.evidence or 'None'} | reason={gap.reason}"
        for gap in gaps
    )

    feedback_text = ""

    if validation_feedback:
        feedback_text = (
            "\n\nA previous plan failed validation.\n"
            f"Validation error: {validation_feedback}\n"
            "Fix this validation issue in the new plan."
        )

    response = client.responses.parse(
        model="gpt-5.6-luna",
        input=[
            {
                "role": "system",
                "content": (
                    "You are a career action planning agent. "
                    "Your job is to turn multiple resume-to-job gaps into a "
                    "coherent and efficient action plan. "

                    "Look for relationships between gaps and avoid recommending "
                    "separate projects when one sequence of work can address "
                    "multiple gaps. "

                    "Prefer the smallest number of realistic actions that address "
                    "the largest number of important gaps. "

                    "Do not add advanced tools, infrastructure, or implementation "
                    "complexity unless they are necessary to address the identified gaps. "

                    "Avoid turning a simple learning objective into an unnecessarily "
                    "production-complex project. "

                    "Prioritize required capabilities and practical dependencies. "

                    "Do not fabricate candidate experience or claim that a short "
                    "project satisfies years-of-experience requirements. "

                    "Dependencies must reference action titles from the same plan. "
                    "When filling addresses_gaps, copy the gap names exactly as provided. "
                    "Do not add labels, status text, explanations, parentheses, or paraphrases."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Create a prioritized career action plan for these gaps:\n\n"
                    f"{gap_text}\n\n"
                    "Guidelines:\n"
                    "- Combine related gaps when practical.\n"
                    "- Reuse or extend existing evidence when possible.\n"
                    "- Use priority 1 for the first action, then 2, 3, and so on.\n"
                    "- Keep dependencies logically ordered.\n"
                    "- If a gap cannot realistically be solved in the short term, "
                    "address it honestly instead of pretending it can be closed."
                    f"{feedback_text}"
                ),
            },
        ],
        text_format=CareerActionPlan,
    )

    return response.output_parsed