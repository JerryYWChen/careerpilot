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
            status=MatchStatus.PARTIAL,
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
            status=MatchStatus.PARTIAL,
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
            status=MatchStatus.MISSING,
            evidence_sources=[],
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
            status=MatchStatus.MISSING,
            evidence_sources=[],
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
            status=MatchStatus.MISSING,
            evidence_sources=[],
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
            evidence_sources=[],
        ),
    },
    policy_rationale=(
        "The resume contains leadership signals but explicitly denies the core "
        "responsibilities of people management."
    ),
)

case_18 = MatchingEvalCase(
    name="Effective Verbal and Written Communication Is Not Assessable",
    resume_text="""
Software Engineer

Experience:
Built and maintained backend services in Python.
Improved API performance and production reliability.
""",
    job_requirements=JobRequirements(
        job_title="Software Engineer",
        seniority_level="unknown",
        summary="Engineering role requiring effective verbal and written communication.",
        requirements=[
            Requirement(
                name="Effective verbal and written communication skills",
                category="skill",
                importance="required",
            )
        ],
    ),
    expected_matches={
        "Effective verbal and written communication skills": ExpectedMatch(
            status=MatchStatus.NOT_ASSESSABLE,
            evidence_sources=[],
        )
    },
    policy_rationale=(
        "A generic communication trait cannot be reliably rejected from resume "
        "silence alone."
    ),
)

case_19 = MatchingEvalCase(
    name="Generic Cross-Functional Collaboration Is Not Assessable",
    resume_text="""
Machine Learning Engineer

Projects:
Developed and evaluated image classification models.
Built automated model-training pipelines.
""",
    job_requirements=JobRequirements(
        job_title="Machine Learning Engineer",
        seniority_level="unknown",
        summary="Role requiring a collaborative cross-functional mindset.",
        requirements=[
            Requirement(
                name="Ability to collaborate cross-functionally",
                category="skill",
                importance="required",
            )
        ],
    ),
    expected_matches={
        "Ability to collaborate cross-functionally": ExpectedMatch(
            status=MatchStatus.NOT_ASSESSABLE,
            evidence_sources=[],
        )
    },
    policy_rationale=(
        "Generic collaboration ability is not reliably disproved because a "
        "resume omits collaboration language."
    ),
)

case_20 = MatchingEvalCase(
    name="Concrete Product and Design Collaboration Is Missing",
    resume_text="""
Backend Engineer

Experience:
Built REST APIs and database integrations using Python and PostgreSQL.
Operated and monitored production backend services.
""",
    job_requirements=JobRequirements(
        job_title="Product Engineer",
        seniority_level="mid",
        summary="Role requiring concrete cross-functional delivery experience.",
        requirements=[
            Requirement(
                name="Experience partnering with Product and Design to deliver launches",
                category="experience",
                importance="required",
            )
        ],
    ),
    expected_matches={
        "Experience partnering with Product and Design to deliver launches": ExpectedMatch(
            status=MatchStatus.MISSING,
            evidence_sources=[],
        )
    },
    policy_rationale=(
        "A concrete work-history responsibility is reasonably expected to be "
        "demonstrable on a resume."
    ),
)

case_21 = MatchingEvalCase(
    name="Validation and Debugging Do Not Establish High Attention to Detail",
    resume_text="""
Data Engineer

Experience:
Implemented schema validation and automated reconciliation across billing datasets.
Diagnosed intermittent data defects, added record-level integrity checks, and reduced
production reconciliation errors by 35 percent.
""",
    job_requirements=JobRequirements(
        job_title="Data Engineer",
        seniority_level="unknown",
        summary="Data role requiring high attention to detail.",
        requirements=[
            Requirement(
                name="High attention to detail",
                category="skill",
                importance="required",
            )
        ],
    ),
    expected_matches={
        "High attention to detail": ExpectedMatch(
            status=MatchStatus.NOT_ASSESSABLE,
            evidence_sources=[],
        )
    },
    policy_rationale=(
        "Validation and debugging establish concrete work activities, but they do "
        "not reliably establish the subjective quality itself."
    ),
)

case_22 = MatchingEvalCase(
    name="Broad Software Work Does Not Establish Attention to Detail",
    resume_text="""
Software Engineer

Experience:
Built production web applications and backend APIs.
Maintained application features and participated in releases.
""",
    job_requirements=JobRequirements(
        job_title="Software Engineer",
        seniority_level="unknown",
        summary="Engineering role requiring attention to detail.",
        requirements=[
            Requirement(
                name="Attention to detail",
                category="skill",
                importance="required",
            )
        ],
    ),
    expected_matches={
        "Attention to detail": ExpectedMatch(
            status=MatchStatus.NOT_ASSESSABLE,
            evidence_sources=[],
        )
    },
    policy_rationale=(
        "Broad software work alone is not reliable contextual evidence for this "
        "generic trait."
    ),
)

case_23 = MatchingEvalCase(
    name="Documentation Does Not Establish Excellent Communication Quality",
    resume_text="""
Platform Engineer

Experience:
Authored API documentation, deployment runbooks, and architecture decision records
for internal engineering teams.
""",
    job_requirements=JobRequirements(
        job_title="Platform Engineer",
        seniority_level="unknown",
        summary="Role requiring excellent written and verbal communication.",
        requirements=[
            Requirement(
                name="Excellent written and verbal communication",
                category="skill",
                importance="required",
            )
        ],
    ),
    expected_matches={
        "Excellent written and verbal communication": ExpectedMatch(
            status=MatchStatus.NOT_ASSESSABLE,
            evidence_sources=[],
        )
    },
    policy_rationale=(
        "Documentation establishes a writing activity, but it does not reliably "
        "establish excellent written or verbal communication quality."
    ),
)

case_24 = MatchingEvalCase(
    name="Executive Presentation Is Directly Demonstrated",
    resume_text="""
Machine Learning Engineer

Experience:
Presented quarterly model-performance results and deployment recommendations to
executive leadership, translating technical findings into business decisions.
""",
    job_requirements=JobRequirements(
        job_title="Applied AI Engineer",
        seniority_level="senior",
        summary="Role requiring executive communication experience.",
        requirements=[
            Requirement(
                name="Presented technical results to executives",
                category="experience",
                importance="required",
            )
        ],
    ),
    expected_matches={
        "Presented technical results to executives": ExpectedMatch(
            status=MatchStatus.MATCHED,
            evidence_sources=[EvidenceSource.EXPERIENCE],
        )
    },
    policy_rationale="The concrete presentation behavior is explicitly evidenced.",
)

case_25 = MatchingEvalCase(
    name="Leadership Scope Is Directly Demonstrated",
    resume_text="""
Engineering Lead

Experience:
Led a team of five engineers, delegated delivery work, facilitated technical
decisions, and conducted recurring coaching sessions.
""",
    job_requirements=JobRequirements(
        job_title="Engineering Lead",
        seniority_level="lead",
        summary="Leadership role requiring experience leading five engineers.",
        requirements=[
            Requirement(
                name="Led a team of 5 engineers",
                category="experience",
                importance="required",
            )
        ],
    ),
    expected_matches={
        "Led a team of 5 engineers": ExpectedMatch(
            status=MatchStatus.MATCHED,
            evidence_sources=[EvidenceSource.EXPERIENCE],
        )
    },
    policy_rationale="The resume directly establishes the required leadership scope.",
)

case_26 = MatchingEvalCase(
    name="Azure and Python Do Not Establish AWS",
    resume_text="""
Cloud Developer

Skills:
Python, Azure

Experience:
Deployed Python services using Azure App Service and Azure Functions.
""",
    job_requirements=JobRequirements(
        job_title="Cloud Engineer",
        seniority_level="unknown",
        summary="Cloud role requiring AWS experience.",
        requirements=[
            Requirement(
                name="AWS experience",
                category="experience",
                importance="required",
            )
        ],
    ),
    expected_matches={
        "AWS experience": ExpectedMatch(
            status=MatchStatus.MISSING,
            evidence_sources=[],
        )
    },
    policy_rationale=(
        "AWS is reasonably resume-demonstrable, and Azure or Python experience "
        "does not establish use of AWS."
    ),
)

case_27 = MatchingEvalCase(
    name="Multitasking Effectiveness Is Not Assessable",
    resume_text="""
Software Engineer

Experience:
Built backend services, fixed production defects, and maintained deployment scripts.
""",
    job_requirements=JobRequirements(
        job_title="Software Engineer",
        seniority_level="unknown",
        summary="Role requiring the ability to manage multiple tasks effectively.",
        requirements=[
            Requirement(
                name="Ability to manage multiple tasks effectively",
                category="skill",
                importance="required",
            )
        ],
    ),
    expected_matches={
        "Ability to manage multiple tasks effectively": ExpectedMatch(
            status=MatchStatus.NOT_ASSESSABLE,
            evidence_sources=[],
        )
    },
    policy_rationale=(
        "Generic resume activities do not reliably establish the subjective "
        "quality of multitasking effectiveness."
    ),
)

case_28 = MatchingEvalCase(
    name="Cross-Functional Activity Does Not Establish Strong Collaboration",
    resume_text="""
Product Engineer

Experience:
Worked with Product and Design to launch a customer onboarding workflow.
Coordinated API changes and user-interface requirements across the teams.
""",
    job_requirements=JobRequirements(
        job_title="Product Engineer",
        seniority_level="unknown",
        summary="Role requiring strong collaboration skills.",
        requirements=[
            Requirement(
                name="Strong collaboration skills",
                category="skill",
                importance="required",
            )
        ],
    ),
    expected_matches={
        "Strong collaboration skills": ExpectedMatch(
            status=MatchStatus.NOT_ASSESSABLE,
            evidence_sources=[],
        )
    },
    policy_rationale=(
        "The resume establishes cross-functional activity, not the subjective "
        "quality of the candidate's collaboration skills."
    ),
)

case_29 = MatchingEvalCase(
    name="Product and Design Collaboration Experience Is Demonstrated",
    resume_text="""
Product Engineer

Experience:
Partnered with Product and Design to define requirements and deliver three customer
workflow launches.
""",
    job_requirements=JobRequirements(
        job_title="Product Engineer",
        seniority_level="unknown",
        summary="Role requiring Product and Design collaboration experience.",
        requirements=[
            Requirement(
                name="Experience collaborating with Product and Design",
                category="experience",
                importance="required",
            )
        ],
    ),
    expected_matches={
        "Experience collaborating with Product and Design": ExpectedMatch(
            status=MatchStatus.MATCHED,
            evidence_sources=[EvidenceSource.EXPERIENCE],
        )
    },
    policy_rationale=(
        "The requirement asks for an observable work activity that the resume "
        "explicitly demonstrates."
    ),
)

case_30 = MatchingEvalCase(
    name="Technical Documentation Experience Is Demonstrated",
    resume_text="""
Platform Engineer

Experience:
Produced API references, deployment runbooks, and architecture documentation for
internal engineering teams.
""",
    job_requirements=JobRequirements(
        job_title="Platform Engineer",
        seniority_level="unknown",
        summary="Role requiring technical documentation experience.",
        requirements=[
            Requirement(
                name="Experience producing technical documentation",
                category="experience",
                importance="required",
            )
        ],
    ),
    expected_matches={
        "Experience producing technical documentation": ExpectedMatch(
            status=MatchStatus.MATCHED,
            evidence_sources=[EvidenceSource.EXPERIENCE],
        )
    },
    policy_rationale=(
        "The requirement asks for the concrete documentation activity, which is "
        "directly evidenced."
    ),
)

case_31 = MatchingEvalCase(
    name="Developer Tooling Capability Remains Resume Assessable",
    resume_text="""
Software Engineer

Projects:
Built a command-line developer tool for validating service configuration, debugged
cross-platform failures, and added regression tests for previously reported defects.
""",
    job_requirements=JobRequirements(
        job_title="Developer Tools Engineer",
        seniority_level="unknown",
        summary="Role requiring hands-on developer tooling capability.",
        requirements=[
            Requirement(
                name="Ability to build and debug personal developer tooling",
                category="skill",
                importance="required",
            )
        ],
    ),
    expected_matches={
        "Ability to build and debug personal developer tooling": ExpectedMatch(
            status=MatchStatus.MATCHED,
            evidence_sources=[EvidenceSource.PROJECTS],
        )
    },
    policy_rationale=(
        "Despite using the word ability, this is a concrete technical capability "
        "that the project reliably demonstrates."
    ),
)

case_32 = MatchingEvalCase(
    name="Hardware and Switch Experience Remains Resume Assessable",
    resume_text="""
Software Engineer

Skills:
Python, PostgreSQL

Experience:
Built backend APIs and database integrations.
""",
    job_requirements=JobRequirements(
        job_title="Data Center Technician",
        seniority_level="entry",
        summary="Role requiring hands-on data-center hardware work.",
        requirements=[
            Requirement(
                name=(
                    "Hands-on experience racking machines, running cable, and "
                    "configuring switches"
                ),
                category="experience",
                importance="required",
            )
        ],
    ),
    expected_matches={
        "Hands-on experience racking machines, running cable, and configuring switches": ExpectedMatch(
            status=MatchStatus.MISSING,
            evidence_sources=[],
        )
    },
    policy_rationale=(
        "Concrete hardware and networking activities are resume-assessable, and "
        "the resume provides no related evidence."
    ),
)

case_33 = MatchingEvalCase(
    name="Onsite Internship Availability Remains Not Assessable",
    resume_text="""
Computer Science Student

Projects:
Built a scheduling application using Python and SQLite.
""",
    job_requirements=JobRequirements(
        job_title="Software Engineering Intern",
        seniority_level="intern",
        summary="Internship requiring onsite availability in Azusa.",
        requirements=[
            Requirement(
                name="Ability to work on-site in Azusa for the full internship",
                category="experience",
                importance="required",
            )
        ],
    ),
    expected_matches={
        "Ability to work on-site in Azusa for the full internship": ExpectedMatch(
            status=MatchStatus.NOT_ASSESSABLE,
            evidence_sources=[],
        )
    },
    policy_rationale=(
        "The resume cannot reliably establish the candidate's current intent, "
        "location logistics, or future availability."
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
    case_18,
    case_19,
    case_20,
    case_21,
    case_22,
    case_23,
    case_24,
    case_25,
    case_26,
    case_27,
    case_28,
    case_29,
    case_30,
    case_31,
    case_32,
    case_33,
]
