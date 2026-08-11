import os

from dotenv import load_dotenv
from openai import OpenAI
from backend.models.analysis import JobRequirements, ResumeMatchResult

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
                    "Use only evidence that appears in the resume. "
                    "Do not invent candidate skills or experience. "
                    "Use 'matched' when the resume provides clear evidence of the requirement "
                    "through direct statements or strong contextual evidence from projects, "
                    "work experience, research, education, or related technologies. "
                    "Do not require the exact requirement keyword to appear in a bullet point. "
                    "Use 'partial' when the requirement is only listed as a skill or is "
                    "supported by weak or indirect evidence. "
                    "Use 'missing' only when there is no reasonable evidence in the resume "
                    "supporting the requirement. "
                    "When using contextual evidence, explain the connection in the reason. "
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

