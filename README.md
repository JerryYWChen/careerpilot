# CareerPilot

CareerPilot is an AI-powered career assistant designed to help users analyze their resumes against job descriptions, understand their strengths and gaps, and receive actionable recommendations for improving their job fit.

The project is currently under active development.

## Current Features

* Upload resumes as PDF files
* Extract text from uploaded PDFs
* Store resume metadata and extracted text using SQLite
* Generate unique resume IDs for uploaded resumes
* Retrieve stored resumes by ID
* Parse job descriptions into structured requirements using AI
* Validate AI-generated structured data with Pydantic
* Match resume evidence against individual job requirements
* Support direct and contextual resume evidence
* Classify requirements as matched, partial, or missing
* Track which resume sections provide evidence for each requirement
* Generate evidence-based explanations for match decisions
* Calculate deterministic weighted resume-to-job match scores
* Identify resume strengths and job requirement gaps
* Generate AI-powered resume improvement recommendations
* Prevent unsupported or fabricated experience from being recommended
* Evaluate AI matching behavior against human-defined expected results
* Evaluate evidence-source attribution against human-defined ground truth
* Run repeated evaluation cases to measure matching consistency
* Log detailed failure information for AI evaluation debugging
* REST API built with FastAPI
* Interactive API testing with Swagger UI

## Current Architecture

CareerPilot uses a structured AI analysis pipeline rather than asking a language model to directly generate an arbitrary match score.

### Resume Pipeline

```text
PDF Upload
    ↓
FastAPI
    ↓
UploadFile
    ↓
PDF Bytes
    ↓
pypdf
    ↓
Extracted Text
    ↓
SQLAlchemy ORM
    ↓
SQLite Database
```

### Job Description Pipeline

```text
Job Description
    ↓
OpenAI API
    ↓
Structured Output
    ↓
Pydantic Validation
    ↓
JobRequirements
```

The structured job requirements include:

* Job title
* Seniority level
* Requirement category
* Required vs. preferred qualifications
* Minimum years of experience when explicitly stated
* Job summary

### Resume Matching Pipeline

```text
Resume Text
      +
JobRequirements
      ↓
OpenAI API
      ↓
Evidence-Based Matching
      ↓
ResumeMatchResult
      ↓
RequirementMatch
├── status
├── evidence
├── evidence_sources
└── reason
```

The language model is responsible for understanding resume evidence and determining how strongly the resume supports each job requirement.

The matcher evaluates the total strength of available evidence. Evidence may come from:

* Skills
* Projects
* Work experience
* Research
* Education
* Certifications
* Related technologies and frameworks
* Implementation details

The system considers both direct and contextual evidence rather than relying only on exact keyword matching.

### Scoring and Analysis Pipeline

```text
ResumeMatchResult
        │
        ├───────────────┐
        ↓               ↓
Deterministic       Match Analysis
Python Scoring          │
        ↓               ├── Strengths
   Match Score          └── Gaps
                            ↓
                    AI Recommendations
                       ↙          ↘
                  Highlight    Strengthen
```

AI is used for semantic understanding and recommendation generation.

Python is used for deterministic business logic such as scoring, requirement completeness validation, strength/gap classification, and evaluation.

### Evaluation Pipeline

```text
MatchingEvalCase
├── Resume Text
├── JobRequirements
└── Expected Matches
        │
        ├── Expected Status
        └── Expected Evidence Sources
                    ↓
              Resume Matcher
                    ↓
          Actual ResumeMatchResult
                    ↓
          Compare Against Ground Truth
                    ↓
                PASS / FAIL
                    ↓
              Repeat N Times
                    ↓
              Consistency %
                    ↓
            Evaluation Summary
```

The evaluation system allows matcher behavior to be tested repeatedly against predefined human-defined expected results.

This provides a repeatable way to detect:

* Incorrect match classifications
* Incorrect evidence-source attribution
* Prompt regressions
* Inconsistent model behavior
* Overly aggressive contextual inference
* Overly conservative evidence interpretation

When an evaluation fails, the runner can report:

* Requirement name
* Expected status
* Actual status
* Expected evidence sources
* Actual evidence sources
* Evidence selected by the model
* Model reasoning

This makes matcher failures easier to diagnose before changing prompts, schemas, or product rules.

## Matching Logic

Each job requirement is classified into one of three states.

### Matched

The resume provides direct evidence or sufficiently strong and reliable contextual evidence supporting the requirement.

Examples include:

* Concrete use of a technology in project or work experience
* Multiple related technologies combined with implementation evidence
* Framework and implementation context that reliably establishes a broader technical requirement
* Concrete research or project evidence supporting the required capability

### Partial

The resume provides relevant evidence, but the evidence is incomplete, indirect, or insufficient to fully establish the requirement.

Examples include:

* A skill appears only in the Skills section without supporting evidence
* Related contextual evidence exists but does not reliably establish the exact requirement
* Relevant experience exists but does not fully satisfy the requirement
* The job requires a certain amount of experience but the resume does not clearly demonstrate that amount

### Missing

The resume provides no reasonable evidence supporting the requirement.

The matcher is instructed not to infer requirements merely from broadly related coursework, fields of study, or weakly related technologies.

## Evidence Sources

CareerPilot tracks which sections of the resume provide evidence supporting each requirement classification.

Current evidence-source categories include:

```text
skills
experience
projects
research
education
certifications
```

A requirement may contain multiple evidence sources.

For example:

```text
Python
├── status: matched
├── evidence_sources
│   ├── skills
│   └── experience
├── evidence
│   └── Python is listed as a skill and used in backend API development.
└── reason
    └── Direct skill evidence is supported by practical implementation experience.
```

A skill that appears only in the Skills section may look like:

```text
AWS
├── status: partial
├── evidence_sources
│   └── skills
└── reason
    └── AWS is listed, but supporting practical evidence is not provided.
```

A missing requirement may contain no evidence sources:

```text
Docker
├── status: missing
├── evidence_sources: []
└── evidence: None
```

Evidence sources represent resume sections that contribute supporting evidence to the requirement analysis.

They are separate from the final match status.

For example, two requirements may both use evidence from Skills and Experience while receiving different statuses because one fully satisfies the job requirement and the other does not.

This separation allows CareerPilot to distinguish:

```text
Where did the evidence come from?
```

from:

```text
Is the evidence sufficient to satisfy the requirement?
```

## Match Score

CareerPilot does not ask the language model to directly generate a match percentage.

Instead, the language model produces structured requirement matches and Python calculates the score deterministically.

Current match values:

```text
matched = 1.0
partial = 0.8
missing = 0.0
```

Job requirements are weighted by importance:

```text
required  = 3
preferred = 1
```

The score is calculated using:

```text
sum(match value × requirement weight)
───────────────────────────────────── × 100
       sum(requirement weights)
```

This makes required qualifications significantly more important than preferred qualifications while keeping the scoring logic predictable and explainable.

The original job requirements remain the source of truth for scoring.

Every requirement must have a corresponding match result. If the AI fails to return a match for a requirement, the scoring system raises an error rather than silently ignoring the requirement and inflating the score.

## Strengths and Gaps

CareerPilot converts structured requirement matches into user-facing strengths and gaps using deterministic Python logic.

```text
matched
    ↓
Strength

partial
    ↓
Gap — existing evidence needs strengthening

missing
    ↓
Gap — no supporting resume evidence
```

A strength contains:

```text
Strength
├── area
├── evidence
└── reason
```

A gap contains:

```text
Gap
├── area
├── status
├── evidence
└── reason
```

Keeping `partial` and `missing` separate allows CareerPilot to distinguish between:

* Skills or qualifications the candidate may already have but needs to demonstrate more clearly
* Skills or experience that are currently unsupported by the resume

## AI Recommendations

CareerPilot generates recommendations based on:

```text
Resume
    +
JobRequirements
    +
Strengths / Gaps
    ↓
OpenAI API
    ↓
Recommendations
```

Recommendations are divided into two categories.

### Highlight

Suggestions for making existing strengths and evidence more visible in the resume.

Examples:

* Emphasize relevant project experience
* Add concrete outcomes when those outcomes are supported by the resume
* Make practical use of an existing skill more explicit

### Strengthen

Suggestions for addressing partial or missing requirements.

Examples:

* Add stronger evidence for an existing skill if that experience is real
* Clarify project or implementation details
* Learn a missing technology
* Build a small project to gain hands-on experience

CareerPilot is explicitly instructed not to fabricate or exaggerate candidate experience.

If a skill is missing, the system should recommend gaining the experience before adding it to the resume rather than suggesting unsupported claims.

## AI Matching Evaluation

CareerPilot includes a repeatable evaluation suite for testing both the behavior and explainability of the resume matcher.

Each evaluation case contains:

```text
MatchingEvalCase
├── name
├── resume_text
├── job_requirements
└── expected_matches
    └── ExpectedMatch
        ├── status
        └── evidence_sources
```

The expected results are human-defined ground truth rather than model-generated answers.

Evidence-source expectations can also be optional, allowing evaluation cases to be migrated or expanded incrementally.

### Current Evaluation Coverage

The current active evaluation suite covers scenarios including:

* Mixed matched, partial, and missing evidence
* Minimum years of experience requirements
* Strong direct implementation evidence
* Completely missing evidence
* Insufficient contextual evidence without an exact keyword
* Framework-to-language contextual evidence
* Backend framework-to-language evidence
* Concrete tool evidence supporting a broader concept
* Explicit skills combined with strong contextual evidence

The suite currently contains nine active evaluation cases.

### Classification Evaluation

The evaluator checks whether the model returns the expected status:

```text
matched
partial
missing
```

If the status differs from human-defined ground truth, the case fails.

### Evidence-Source Evaluation

The evaluator can also compare expected and actual evidence sources.

For example:

```text
Expected:
status = matched
sources = [skills, experience]

Actual:
status = matched
sources = [skills, experience]

→ PASS
```

If the classification is correct but the evidence attribution is incorrect:

```text
Expected:
sources = [skills, experience]

Actual:
sources = [skills]

→ FAIL
```

Evidence-source comparison ignores ordering.

Therefore:

```text
[skills, experience]
```

and:

```text
[experience, skills]
```

are treated as equivalent.

### Repeated Consistency Evaluation

Each case can be executed multiple times to measure whether the model consistently produces the expected result.

Example:

```text
=== Backend Framework Context Supports Language ===
Run 1: PASS
Run 2: PASS
Run 3: PASS
Consistency: 3/3 (100%)
```

This allows CareerPilot to measure not only whether a model can produce the correct answer, but whether it can produce that behavior consistently across repeated runs.

### Failure Diagnostics

When a run fails, the evaluator provides detailed diagnostics.

Example:

```text
FAIL: Python
expected status: missing
actual status: partial

expected sources: []
actual sources: [projects]

evidence:
The resume describes related machine learning project experience.

reason:
The model interpreted the projects as indirect contextual evidence.
```

This allows failures to be reviewed before changing the matcher prompt or ground-truth expectations.

### Current Evaluation Baseline

The latest full regression run contains:

```text
Active evaluation cases: 9
Runs per case: 3
Total evaluation runs: 27
Passing runs: 26
Overall run accuracy: 96.3%
```

Eight active cases achieved:

```text
3/3 passing
100% consistency
```

One contextual-evidence boundary case produced:

```text
2/3 passing
67% consistency
```

The boundary case involves highly related contextual evidence that does not explicitly establish the required skill.

The model may occasionally classify this evidence as `partial` rather than `missing`.

This case is intentionally retained because it helps measure uncertainty around the boundary between insufficient evidence and weak indirect evidence.

The current evaluation baseline should not be interpreted as 96.3% accuracy across all possible resumes and job descriptions.

It represents performance only on the current human-defined evaluation suite.

New real-world failure patterns can be converted into additional evaluation cases before matcher behavior or prompts are changed.

## Tech Stack

### Backend

* Python
* FastAPI
* Uvicorn
* Pydantic

### Database

* SQLite
* SQLAlchemy

### Document Processing

* pypdf

### AI

* OpenAI API
* Structured Outputs
* Pydantic-based AI response validation
* Evidence-based requirement matching
* Ground-truth matching evaluations
* Evidence-source evaluation
* Repeated consistency testing

### Frontend

* TBD

## API

### Upload Resume

`POST /resume`

Uploads a PDF resume, extracts its text, stores the resume data, and returns a unique resume ID.

Example response:

```json
{
  "resume_id": 1,
  "filename": "Resume_AI.pdf",
  "size": 133981,
  "text_preview": "..."
}
```

### Retrieve Resume

`GET /resume/{resume_id}`

Retrieves metadata for a stored resume.

Example response:

```json
{
  "resume_id": 1,
  "filename": "Resume_AI.pdf",
  "created_at": "2026-08-09T03:37:44.840814"
}
```

If the resume does not exist, the API returns:

```text
404 Not Found
```

### Analyze Resume

`POST /resume/{resume_id}/analyze`

Runs the complete CareerPilot resume analysis pipeline against a provided job description.

The endpoint:

1. Retrieves the stored resume from SQLite
2. Extracts structured requirements from the job description
3. Matches resume evidence against every requirement
4. Classifies requirements as matched, partial, or missing
5. Identifies the resume sections supporting each requirement
6. Calculates a deterministic weighted match score
7. Builds strengths and gaps
8. Generates actionable AI recommendations

Example request:

```json
{
  "job_description": "We are looking for a Software Engineer with Python and FastAPI experience. AWS experience is preferred."
}
```

Example response structure:

```json
{
  "resume_id": 2,
  "filename": "Resume_Software.pdf",
  "job": {
    "job_title": "Software Engineer",
    "seniority_level": "unknown",
    "summary": "Software Engineer role requiring Python and FastAPI experience; AWS experience is preferred.",
    "requirements": [
      {
        "name": "Python",
        "category": "skill",
        "importance": "required",
        "minimum_years": null
      },
      {
        "name": "FastAPI",
        "category": "skill",
        "importance": "required",
        "minimum_years": null
      },
      {
        "name": "AWS",
        "category": "skill",
        "importance": "preferred",
        "minimum_years": null
      }
    ]
  },
  "match_score": 42.86,
  "strengths": [
    {
      "area": "Python",
      "evidence": "Resume evidence supporting practical Python experience.",
      "reason": "The resume provides sufficient evidence of Python usage."
    }
  ],
  "gaps": [
    {
      "area": "FastAPI",
      "status": "missing",
      "evidence": null,
      "reason": "The resume does not provide evidence of FastAPI experience."
    }
  ],
  "recommendations": {
    "highlight": [
      "Emphasize existing Python experience with concrete project evidence and outcomes."
    ],
    "strengthen": [
      "Gain hands-on FastAPI experience through a small API project before adding it as demonstrated experience."
    ]
  }
}
```

## AI Analysis Design

CareerPilot uses structured AI outputs rather than relying on free-form model responses.

### Job Requirement Schema

```text
JobRequirements
├── job_title
├── seniority_level
├── summary
└── requirements[]
    ├── name
    ├── category
    ├── importance
    └── minimum_years
```

Requirement categories currently include:

* Skill
* Experience
* Education
* Certification

Requirement importance is classified as:

* Required
* Preferred

### Resume Match Schema

```text
ResumeMatchResult
└── matches[]
    ├── requirement_name
    ├── status
    ├── evidence
    ├── evidence_sources[]
    └── reason
```

Evidence sources currently include:

```text
skills
experience
projects
research
education
certifications
```

### Match Analysis Schema

```text
MatchAnalysis
├── strengths[]
│   ├── area
│   ├── evidence
│   └── reason
│
└── gaps[]
    ├── area
    ├── status
    ├── evidence
    └── reason
```

### Recommendation Schema

```text
Recommendations
├── highlight[]
└── strengthen[]
```

### Evaluation Schema

```text
MatchingEvalCase
├── name
├── resume_text
├── job_requirements
└── expected_matches
    └── ExpectedMatch
        ├── status
        └── evidence_sources
```

Pydantic models and enums validate AI-generated structured data and evaluation expectations before they enter downstream business logic.

## Development Progress

### Backend Foundation

* [x] Set up Git and GitHub
* [x] Create Python virtual environment
* [x] Set up FastAPI and Uvicorn
* [x] Add Swagger API documentation
* [x] Configure environment variables for secrets

### Resume Pipeline

* [x] Upload PDF resumes
* [x] Read uploaded files as bytes
* [x] Extract text from PDFs
* [x] Create Resume ORM model
* [x] Set up SQLite database
* [x] Persist resume data
* [x] Generate resume IDs
* [x] Retrieve resumes by ID
* [x] Handle missing resumes with HTTP 404

### AI Pipeline

* [x] Integrate OpenAI API
* [x] Secure API credentials using environment variables
* [x] Define structured job requirement schemas
* [x] Add Pydantic validation
* [x] Extract structured requirements from job descriptions
* [x] Match resume evidence against individual job requirements
* [x] Support direct and contextual resume evidence
* [x] Classify requirements as matched, partial, or missing
* [x] Track evidence sources for requirement matches
* [x] Generate evidence-based explanations
* [x] Calculate deterministic weighted match scores
* [x] Detect incomplete AI match results before scoring
* [x] Generate strengths and gaps
* [x] Generate resume improvement recommendations
* [x] Connect the full analysis pipeline to FastAPI

### AI Evaluation

* [x] Define structured matching evaluation cases
* [x] Add human-defined expected match results
* [x] Automatically compare AI output against ground truth
* [x] Detect missing requirement matches
* [x] Add repeated evaluation runs
* [x] Measure per-case matching consistency
* [x] Calculate overall evaluation accuracy
* [x] Add detailed failure logging with evidence and reasoning
* [x] Add evidence-source ground truth
* [x] Evaluate evidence-source attribution
* [x] Detect evidence-source mismatches
* [x] Establish Status + Evidence Source Eval v1 baseline
* [x] Identify and retain contextual-evidence boundary cases
* [ ] Expand evaluation coverage with real-world resume and job-description cases
* [ ] Track evaluation results across matcher or prompt versions

### Planned

* [ ] Expand requirement evidence analysis and explainability
* [ ] Analyze candidate experience and estimated relevant experience
* [ ] Add recommendation prioritization
* [ ] Expand AI evaluation coverage using real-world failures
* [ ] Generate interview questions based on resume and job gaps
* [ ] Add mock interview feedback
* [ ] Build user authentication
* [ ] Build frontend application
* [ ] Deploy to production

## Project Structure

```text
careerpilot/
├── backend/
│   ├── database/
│   ├── evals/
│   │   ├── matching_cases.py
│   │   └── run_matching_eval.py
│   ├── models/
│   │   ├── resume.py
│   │   └── analysis.py
│   ├── services/
│   │   ├── resume_service.py
│   │   ├── ai_service.py
│   │   └── scoring_service.py
│   └── main.py
├── .env
├── .gitignore
└── README.md
```

> `.env` contains local secrets such as API credentials and is excluded from Git.

## Status

The core CareerPilot v0.1 resume analysis pipeline is functional end-to-end.

CareerPilot can currently process a PDF resume, store it, analyze a job description, evaluate resume evidence against structured requirements, calculate an explainable match score, identify strengths and gaps, and generate actionable resume recommendations.

The matcher now also tracks which resume sections provide evidence for each requirement, allowing CareerPilot to distinguish the source of the evidence from whether that evidence is sufficient to satisfy the job requirement.

The project includes a repeatable AI evaluation suite with human-defined ground truth, repeated consistency testing, status evaluation, evidence-source evaluation, aggregate accuracy reporting, and detailed failure diagnostics.

The latest Status + Evidence Source Eval v1 regression contains nine active cases executed three times each. Twenty-six of twenty-seven runs passed, producing a 96.3% overall run accuracy on the current evaluation suite. Eight cases achieved 100% consistency, while one contextual-evidence boundary case remains intentionally tracked for model consistency.

The next development focus is expanding requirement-level explainability, analyzing candidate experience, expanding evaluation coverage with real-world cases, and continuing toward a user-facing frontend.
