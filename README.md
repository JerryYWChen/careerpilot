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
* Calculate deterministic weighted resume-to-job match scores
* Identify resume strengths and job requirement gaps
* Generate AI-powered resume improvement recommendations
* Prevent unsupported or fabricated experience from being recommended
* Evaluate AI matching behavior against human-defined expected results
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
matched / partial / missing
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

Python is used for deterministic business logic such as scoring, requirement completeness validation, and strength/gap classification.

### Evaluation Pipeline

```text
MatchingEvalCase
├── Resume Text
├── JobRequirements
└── Expected Matches
        ↓
Resume Matcher
        ↓
Actual ResumeMatchResult
        ↓
Compare Against
Human-Defined Ground Truth
        ↓
PASS / FAIL
        ↓
Repeat N Times
        ↓
Consistency %
        ↓
Evaluation Summary
```

The evaluation system allows matcher behavior to be tested repeatedly against predefined expected results.

This provides a repeatable way to detect:

* Incorrect match classifications
* Prompt regressions
* Inconsistent model behavior
* Overly aggressive contextual inference
* Overly conservative evidence interpretation

When an evaluation fails, the runner records:

* Requirement name
* Expected status
* Actual status
* Evidence selected by the model
* Model reasoning

This makes matcher failures easier to diagnose before changing prompts or product rules.

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
* Strong related context exists, but the exact required skill is not sufficiently established
* Relevant experience exists but does not fully satisfy the requirement
* The job requires a certain amount of experience but the resume does not clearly demonstrate that amount

### Missing

The resume provides no reasonable evidence supporting the requirement.

The matcher is instructed not to infer requirements merely from broadly related coursework, fields of study, or weakly related technologies.

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

CareerPilot includes a repeatable evaluation suite for testing the behavior and consistency of the resume matcher.

Each evaluation case contains:

```text
MatchingEvalCase
├── name
├── resume_text
├── job_requirements
└── expected_matches
```

The expected matches are human-defined ground truth rather than model-generated answers.

### Current Evaluation Coverage

The current evaluation suite covers scenarios including:

* Mixed matched, partial, and missing evidence
* Minimum years of experience requirements
* Strong direct implementation evidence
* Completely missing evidence
* Strong contextual evidence without an exact keyword
* Framework-to-language contextual evidence
* Backend framework-to-language evidence
* Concrete tool evidence supporting a broader concept
* Weak contextual evidence that should not be over-inferred
* Explicit skills combined with strong contextual evidence

### Repeated Consistency Evaluation

Each case can be executed multiple times to measure whether the model consistently produces the expected classification.

Example:

```text
=== Skills Plus Strong Context ===
Run 1: PASS
Run 2: PASS
Run 3: PASS
Consistency: 3/3 (100%)
```

The evaluation runner also generates an overall summary:

```text
=== Evaluation Summary ===
Mixed Evidence: 3/3 (100%)
Insufficient Years: 3/3 (100%)
Strong Direct Evidence: 3/3 (100%)
No Evidence: 3/3 (100%)
Strong Contextual Evidence Without Exact Keyword: 3/3 (100%)
Framework Context Supports Language: 3/3 (100%)
Backend Framework Context Supports Language: 3/3 (100%)
Concrete Tool Evidence Supports Broader Concept: 3/3 (100%)
Weak Contextual Evidence Is Not Sufficient: 3/3 (100%)
Skills Plus Strong Context: 3/3 (100%)

Overall Run Accuracy: 30/30 (100.0%)
```

This represents the current Matcher Eval v1 baseline:

```text
Evaluation cases: 10
Runs per case: 3
Total evaluation runs: 30
Passing runs: 30
Current baseline: 100%
```

This baseline applies only to the current evaluation suite and should not be interpreted as 100% accuracy across all possible resumes and job descriptions.

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
* Ground-truth matching evaluations
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
5. Calculates a deterministic weighted match score
6. Builds strengths and gaps
7. Generates actionable AI recommendations

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
      "reason": "The resume provides direct or strong contextual evidence of Python usage."
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
    └── reason
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

Pydantic models and enums validate AI-generated structured data before it enters downstream business logic.

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
* [x] Establish Matcher Eval v1 baseline
* [ ] Expand evaluation coverage with real-world resume and job-description cases
* [ ] Track evaluation results across matcher or prompt versions

### Planned

* [ ] Candidate experience analysis and estimated relevant experience
* [ ] Recommendation prioritization
* [ ] Expanded AI evaluation coverage
* [ ] Interview question generation
* [ ] Mock interview feedback
* [ ] User authentication
* [ ] Frontend application
* [ ] Production deployment

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

The project also includes a repeatable AI matching evaluation suite with human-defined ground truth, repeated consistency testing, aggregate accuracy reporting, and detailed failure diagnostics.

The current Matcher Eval v1 baseline contains 10 evaluation cases executed three times each, with 30 of 30 evaluation runs passing in the current baseline.

The next development focus is expanding evaluation coverage with real-world cases, analyzing candidate experience, improving recommendation prioritization, and continuing toward a user-facing frontend.
