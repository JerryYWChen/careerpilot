from pydantic import BaseModel

from backend.models.analysis import (
    JobRequirements,
    MatchStatus,
    Requirement,
    EvidenceSource,
)

class ExpectedMatch(BaseModel):
    status: MatchStatus
    evidence_sources: list[EvidenceSource]

class MatchingEvalCase(BaseModel):
    name: str
    resume_text: str
    job_requirements: JobRequirements
    expected_matches: dict[str, ExpectedMatch]

case_1 = MatchingEvalCase(
    name="Mixed Evidence",
    resume_text="""
Software Engineer

Skills:
Python, AWS

Experience:
Built backend REST APIs using Python.
""",
    job_requirements=JobRequirements(
        job_title="Backend Engineer",
        seniority_level="unknown",
        summary="Backend role requiring Python, AWS, and Docker.",
        requirements=[
            Requirement(
                name="Python",
                category="skill",
                importance="required"
            ),
            Requirement(
                name="AWS",
                category="skill",
                importance="required"
            ),
            Requirement(
                name="Docker",
                category="skill",
                importance="required"
            ),
        ]
    ),
    expected_matches={
        "Python": ExpectedMatch(
            status=MatchStatus.MATCHED,
            evidence_sources=[
                EvidenceSource.SKILLS,
                EvidenceSource.EXPERIENCE,
            ],
        ),
        "AWS": ExpectedMatch(
            status=MatchStatus.PARTIAL,
            evidence_sources=[
                EvidenceSource.SKILLS,
            ],
        ),
        "Docker": ExpectedMatch(
            status=MatchStatus.MISSING,
            evidence_sources=[],
        ),
    }
)

case_2 = MatchingEvalCase(
    name="Insufficient Years",
    resume_text="""
Software Engineer

Skills:
Python

Experience:
Software Engineer — 2025 to 2026
Built backend applications using Python.
""",
    job_requirements=JobRequirements(
        job_title="Backend Engineer",
        seniority_level="mid",
        summary="Backend role requiring at least 3 years of Python experience.",
        requirements=[
            Requirement(
                name="Python",
                category="experience",
                importance="required",
                minimum_years=3
            )
        ]
    ),
    expected_matches={
        "Python": ExpectedMatch(
            status=MatchStatus.PARTIAL,
            evidence_sources=[
                EvidenceSource.SKILLS,
                EvidenceSource.EXPERIENCE,
            ],
        ),
    }
)

case_3 = MatchingEvalCase(
    name="Strong Direct Evidence",
    resume_text="""
Software Engineer

Skills:
Python, Docker

Projects:
Containerized a FastAPI application using Docker.
Created a Dockerfile, built Docker images, and ran the application in containers.
""",
    job_requirements=JobRequirements(
        job_title="Backend Engineer",
        seniority_level="unknown",
        summary="Backend role requiring Docker experience.",
        requirements=[
            Requirement(
                name="Docker",
                category="skill",
                importance="required"
            )
        ]
    ),
    expected_matches={
        "Docker": ExpectedMatch(
            status=MatchStatus.MATCHED,
            evidence_sources=[
                EvidenceSource.SKILLS,
                EvidenceSource.PROJECTS,
            ],
        ),
    }
)

case_4 = MatchingEvalCase(
    name="No Evidence",
    resume_text="""
Software Engineer

Skills:
Java, Spring Boot

Experience:
Built backend REST APIs using Java and Spring Boot.
Developed enterprise applications and database integrations.
""",
    job_requirements=JobRequirements(
        job_title="Backend Engineer",
        seniority_level="unknown",
        summary="Backend role requiring Python experience.",
        requirements=[
            Requirement(
                name="Python",
                category="skill",
                importance="required"
            )
        ]
    ),
    expected_matches={
        "Python": ExpectedMatch(
            status=MatchStatus.MISSING,
            evidence_sources=[],
        ),
    }
)

case_5 = MatchingEvalCase(
    name="Insufficient Context Without Exact Keyword",
    resume_text="""
Machine Learning Engineer

Skills:
PyTorch, TensorFlow, Deep Learning

Projects:
Built deep learning models for image classification.
Developed an LLM evaluation pipeline for model benchmarking.
Implemented training and evaluation workflows for machine learning experiments.
""",
    job_requirements=JobRequirements(
        job_title="Machine Learning Engineer",
        seniority_level="unknown",
        summary="ML role requiring Python experience.",
        requirements=[
            Requirement(
                name="Python",
                category="skill",
                importance="required"
            )
        ]
    ),
    expected_matches={
        "Python": ExpectedMatch(
            status=MatchStatus.MISSING,
            evidence_sources=[],
        ),
    }
)

case_6 = MatchingEvalCase(
    name="Framework Context Supports Language",
    resume_text="""
Frontend Developer

Skills:
React, Redux

Projects:
Built a responsive dashboard using React and Redux.
Implemented reusable components and client-side state management.
""",
    job_requirements=JobRequirements(
        job_title="Frontend Engineer",
        seniority_level="unknown",
        summary="Frontend role requiring JavaScript experience.",
        requirements=[
            Requirement(
                name="JavaScript",
                category="skill",
                importance="required"
            )
        ]
    ),
    expected_matches={
        "JavaScript": ExpectedMatch(
            status=MatchStatus.MATCHED,
            evidence_sources=[
                EvidenceSource.SKILLS,
                EvidenceSource.PROJECTS,
            ],
        ),
    }
)

case_7 = MatchingEvalCase(
    name="Backend Framework Context Supports Language",
    resume_text="""
Backend Developer

Skills:
FastAPI, SQLAlchemy

Projects:
Built REST APIs with FastAPI and SQLAlchemy.
Implemented database models, API endpoints, and CRUD operations.
""",
    job_requirements=JobRequirements(
        job_title="Backend Engineer",
        seniority_level="unknown",
        summary="Backend role requiring Python experience.",
        requirements=[
            Requirement(
                name="Python",
                category="skill",
                importance="required"
            )
        ]
    ),
    expected_matches={
        "Python": ExpectedMatch(
            status=MatchStatus.MATCHED,
            evidence_sources=[
                EvidenceSource.SKILLS,
                EvidenceSource.PROJECTS,
            ],
        ),
    }
)

case_8 = MatchingEvalCase(
    name="Concrete Tool Evidence Supports Broader Concept",
    resume_text="""
Software Engineer

Projects:
Created Dockerfiles and containerized a REST API.
Built Docker images and ran multiple services using Docker Compose.
""",
    job_requirements=JobRequirements(
        job_title="Backend Engineer",
        seniority_level="unknown",
        summary="Backend role requiring containerization experience.",
        requirements=[
            Requirement(
                name="Containerization",
                category="skill",
                importance="required"
            )
        ]
    ),
    expected_matches={
        "Containerization": ExpectedMatch(
            status=MatchStatus.MATCHED,
            evidence_sources=[
                EvidenceSource.PROJECTS,
            ],
        ),
    }
)

case_9 = MatchingEvalCase(
    name="Skills Plus Strong Context",
    resume_text="""
Machine Learning Engineer

Skills:
Python, PyTorch, TensorFlow

Projects:
Developed a deep learning image classification pipeline using PyTorch.
Implemented data preprocessing, model training, and evaluation workflows.
Built an LLM evaluation pipeline for benchmarking model performance.
""",
    job_requirements=JobRequirements(
        job_title="Machine Learning Engineer",
        seniority_level="unknown",
        summary="ML role requiring Python experience.",
        requirements=[
            Requirement(
                name="Python",
                category="skill",
                importance="required"
            )
        ]
    ),
    expected_matches={
        "Python": ExpectedMatch(
            status=MatchStatus.MATCHED,
            evidence_sources=[
                EvidenceSource.SKILLS,
                EvidenceSource.PROJECTS,
            ],
        ),
    }
)

MATCHING_EVAL_CASES = [
    case_1,
    case_2,
    case_3,
    case_4,
    case_5,
    case_6,
    case_7,
    case_8,
    case_9,
]