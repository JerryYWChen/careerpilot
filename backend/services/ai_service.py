import os

from dotenv import load_dotenv
from openai import OpenAI
from backend.models.analysis import JobRequirements, ResumeMatchResult, MatchAnalysis, Recommendations

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
