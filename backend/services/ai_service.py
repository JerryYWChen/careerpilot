import os

from dotenv import load_dotenv
from openai import OpenAI
from backend.models.analysis import JobRequirements

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

