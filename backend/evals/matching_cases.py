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
    policy_rationale: str | None = None

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

case_10 = MatchingEvalCase(
    name="Next.js Does Not Reliably Establish TypeScript",
    resume_text="""
Frontend Developer

Skills:
Next.js, React

Projects:
Built a marketing site with Next.js and reusable React components.
""",
    job_requirements=JobRequirements(
        job_title="Frontend Engineer",
        seniority_level="unknown",
        summary="Frontend role requiring TypeScript experience.",
        requirements=[
            Requirement(
                name="TypeScript",
                category="skill",
                importance="required"
            )
        ]
    ),
    expected_matches={
        "TypeScript": ExpectedMatch(
            status=MatchStatus.PARTIAL,
            evidence_sources=[
                EvidenceSource.SKILLS,
                EvidenceSource.PROJECTS,
            ],
        ),
    },
    policy_rationale=(
        "Next.js supports both JavaScript and TypeScript. The framework evidence "
        "is relevant but does not establish that TypeScript was used."
    ),
)

case_11 = MatchingEvalCase(
    name="Container Experience Without Orchestration",
    resume_text="""
Backend Developer

Skills:
Docker, Docker Compose

Projects:
Containerized a web API and database.
Used Docker Compose to run the services locally.
""",
    job_requirements=JobRequirements(
        job_title="Platform Engineer",
        seniority_level="unknown",
        summary="Platform role requiring Kubernetes experience.",
        requirements=[
            Requirement(
                name="Kubernetes",
                category="skill",
                importance="required"
            )
        ]
    ),
    expected_matches={
        "Kubernetes": ExpectedMatch(
            status=MatchStatus.PARTIAL,
            evidence_sources=[
                EvidenceSource.SKILLS,
                EvidenceSource.PROJECTS,
            ],
        ),
    },
    policy_rationale=(
        "Containerization is relevant preparation, but Docker Compose does not "
        "demonstrate Kubernetes cluster or orchestration experience."
    ),
)

case_12 = MatchingEvalCase(
    name="Compound AND Requirement Partially Satisfied",
    resume_text="""
Backend Developer

Skills:
Python, FastAPI

Projects:
Built and deployed REST APIs using Python and FastAPI.
""",
    job_requirements=JobRequirements(
        job_title="Backend Engineer",
        seniority_level="unknown",
        summary="Backend role requiring both Python and Django.",
        requirements=[
            Requirement(
                name="Python and Django",
                category="skill",
                importance="required"
            )
        ]
    ),
    expected_matches={
        "Python and Django": ExpectedMatch(
            status=MatchStatus.PARTIAL,
            evidence_sources=[
                EvidenceSource.SKILLS,
                EvidenceSource.PROJECTS,
            ],
        ),
    },
    policy_rationale=(
        "Python is strongly established, but a conjunctive requirement is not "
        "fully satisfied because the resume provides no Django evidence."
    ),
)

case_13 = MatchingEvalCase(
    name="Compound OR Requirement Satisfied",
    resume_text="""
Cloud Developer

Skills:
Azure, C#

Experience:
Deployed services using Azure App Service and Azure Blob Storage.
Implemented event-driven processing with Azure Functions.
""",
    job_requirements=JobRequirements(
        job_title="Cloud Engineer",
        seniority_level="unknown",
        summary="Cloud role accepting either AWS or Azure experience.",
        requirements=[
            Requirement(
                name="AWS or Azure cloud experience",
                category="experience",
                importance="required"
            )
        ]
    ),
    expected_matches={
        "AWS or Azure cloud experience": ExpectedMatch(
            status=MatchStatus.MATCHED,
            evidence_sources=[
                EvidenceSource.SKILLS,
                EvidenceSource.EXPERIENCE,
            ],
        ),
    },
    policy_rationale=(
        "An OR requirement needs only one alternative, and the resume contains "
        "direct practical Azure evidence."
    ),
)

case_14 = MatchingEvalCase(
    name="AWS Platform and Lambda Are Separate Requirements",
    resume_text="""
Cloud Engineer

Skills:
AWS, Azure Functions

Experience:
Deployed applications to Amazon EC2 and stored assets in Amazon S3.

Projects:
Built an event-driven image processor using Azure Functions.
""",
    job_requirements=JobRequirements(
        job_title="Cloud Engineer",
        seniority_level="unknown",
        summary="Cloud role requiring AWS platform and AWS Lambda experience.",
        requirements=[
            Requirement(
                name="AWS cloud experience",
                category="experience",
                importance="required"
            ),
            Requirement(
                name="AWS Lambda",
                category="skill",
                importance="required"
            ),
        ]
    ),
    expected_matches={
        "AWS cloud experience": ExpectedMatch(
            status=MatchStatus.MATCHED,
            evidence_sources=[
                EvidenceSource.SKILLS,
                EvidenceSource.EXPERIENCE,
            ],
        ),
        "AWS Lambda": ExpectedMatch(
            status=MatchStatus.PARTIAL,
            evidence_sources=[
                EvidenceSource.SKILLS,
                EvidenceSource.EXPERIENCE,
                EvidenceSource.PROJECTS,
            ],
        ),
    },
    policy_rationale=(
        "EC2 and S3 establish broad AWS experience. Azure Functions supplies "
        "related serverless evidence, but it does not prove direct Lambda use."
    ),
)

case_15 = MatchingEvalCase(
    name="Experience Exactly Meets Minimum",
    resume_text="""
Backend Engineer

Skills:
Python

Experience:
Python Backend Engineer — January 2022 to January 2025
Built and maintained production Python APIs throughout this role.
""",
    job_requirements=JobRequirements(
        job_title="Backend Engineer",
        seniority_level="mid",
        summary="Backend role requiring at least three years of Python experience.",
        requirements=[
            Requirement(
                name="Python experience",
                category="experience",
                importance="required",
                minimum_years=3
            )
        ]
    ),
    expected_matches={
        "Python experience": ExpectedMatch(
            status=MatchStatus.MATCHED,
            evidence_sources=[
                EvidenceSource.SKILLS,
                EvidenceSource.EXPERIENCE,
            ],
        ),
    },
    policy_rationale=(
        "The resume explicitly establishes exactly three years of relevant "
        "experience, which meets the stated threshold."
    ),
)

case_16 = MatchingEvalCase(
    name="Overlapping Experience Does Not Add Linearly",
    resume_text="""
Backend Engineer

Skills:
Python

Experience:
Python Engineer — January 2024 to January 2026
Built backend APIs in Python.

Freelance Python Developer — January 2024 to January 2026
Maintained a Python automation service alongside the full-time role.
""",
    job_requirements=JobRequirements(
        job_title="Backend Engineer",
        seniority_level="mid",
        summary="Backend role requiring at least three years of Python experience.",
        requirements=[
            Requirement(
                name="Python experience",
                category="experience",
                importance="required",
                minimum_years=3
            )
        ]
    ),
    expected_matches={
        "Python experience": ExpectedMatch(
            status=MatchStatus.PARTIAL,
            evidence_sources=[
                EvidenceSource.SKILLS,
                EvidenceSource.EXPERIENCE,
            ],
        ),
    },
    policy_rationale=(
        "The roles overlap completely, so they establish two elapsed years of "
        "experience rather than four."
    ),
)

case_17 = MatchingEvalCase(
    name="Leadership Signals Without People Management",
    resume_text="""
Senior Software Engineer

Experience:
Led architecture discussions, mentored two junior engineers, coordinated releases,
presented quarterly roadmaps, and served as technical lead for a migration.

This was an individual-contributor role. I had no direct reports and did not perform
hiring, compensation, or performance reviews.
""",
    job_requirements=JobRequirements(
        job_title="Engineering Manager",
        seniority_level="lead",
        summary="Management role requiring people management experience.",
        requirements=[
            Requirement(
                name="People management experience",
                category="experience",
                importance="required"
            )
        ]
    ),
    expected_matches={
        "People management experience": ExpectedMatch(
            status=MatchStatus.MISSING,
            evidence_sources=[
                EvidenceSource.EXPERIENCE,
            ],
        ),
    },
    policy_rationale=(
        "The resume contains leadership signals but explicitly denies the core "
        "responsibilities of people management."
    ),
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
    case_10,
    case_11,
    case_12,
    case_13,
    case_14,
    case_15,
    case_16,
    case_17,
]
