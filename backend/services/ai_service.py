import os

from dotenv import load_dotenv
from openai import OpenAI
from backend.models.analysis import Gap, JobRequirements, ResumeMatchResult, MatchAnalysis, Recommendations, RecommendationReview

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

def generate_recommendations(
    resume_text: str,
    job_requirements: JobRequirements,
    match_analysis: MatchAnalysis
) -> Recommendations:

    response = client.responses.parse(
        model="gpt-5.6-luna",
        input=[
            {
                "role": "system",
                "content": (
                    "Analyze the resume against the provided job requirements "
                    "and match analysis. "
                    "For matched requirements, recommend how the candidate "
                    "can highlight the relevant experience or evidence in "
                    "the resume. "
                    "For partial requirements, recommend how the candidate "
                    "can strengthen the existing evidence or clarify the "
                    "experience in the resume. "
                    "For missing requirements, recommend learning the skill "
                    "or building a small project to gain relevant experience. "
                    "Do not ask the candidate to add skills, experience, "
                    "or achievements that are not supported by the resume. "
                    "Never fabricate or exaggerate candidate experience."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Resume:\n{resume_text}\n\n"
                    f"Job requirements:\n"
                    f"{job_requirements.model_dump_json()}\n\n"
                    f"Match analysis:\n"
                    f"{match_analysis.model_dump_json()}"
                ),
            },
        ],
        text_format=Recommendations,
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