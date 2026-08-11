# CareerPilot

CareerPilot is an AI-powered career assistant designed to help users analyze their resumes against job descriptions and prepare for interviews.

The project is currently under active development.

## Current Features

- Upload resumes as PDF files
- Extract text from uploaded PDFs
- Store resume metadata and extracted text using SQLite
- Generate unique resume IDs for uploaded resumes
- Retrieve stored resumes by ID
- Parse job descriptions into structured requirements using AI
- Match resume evidence against individual job requirements
- Classify requirements as matched, partial, or missing
- Calculate deterministic resume-to-job match scores
- Validate AI-generated structured data with Pydantic
- REST API built with FastAPI
- Interactive API testing with Swagger UI

## Current Architecture

CareerPilot currently follows three main backend pipelines.

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

- Job title
- Seniority level
- Requirement category
- Required vs. preferred qualifications
- Minimum years of experience when explicitly stated
- Job summary

### Resume Matching Pipeline

```text
Resume Text
      +
JobRequirements
      ↓
OpenAI API
      ↓
Structured Evidence Matching
      ↓
ResumeMatchResult
      ↓
matched / partial / missing
      ↓
Deterministic Python Scoring
      ↓
Match Score
```

The AI is responsible for understanding resume evidence and classifying how well each requirement is supported.

Python is responsible for calculating the final match score using deterministic scoring rules.

## Matching Logic

Each job requirement is classified into one of three match states:

- `matched` — the resume provides clear direct or strong contextual evidence
- `partial` — the skill is mentioned or partially supported, but evidence is incomplete
- `missing` — the resume provides no reasonable evidence for the requirement

Current match values:

```text
matched  = 1.0
partial  = 0.8
missing  = 0.0
```

Job requirements are also weighted based on importance:

```text
required  = 3
preferred = 1
```

The final match score is calculated deterministically in Python rather than generated directly by the language model.

This allows CareerPilot to use AI for semantic understanding while keeping scoring logic predictable and explainable.

## Tech Stack

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic

### Database

- SQLite
- SQLAlchemy

### Document Processing

- pypdf

### AI

- OpenAI API
- Structured Outputs
- Pydantic-based AI response validation

### Frontend

- TBD

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

Analyzes a stored resume against a job description.

The analysis pipeline:

1. Retrieves the stored resume from the database
2. Extracts structured requirements from the job description
3. Matches resume evidence against every requirement
4. Classifies each requirement as `matched`, `partial`, or `missing`
5. Calculates a deterministic weighted match score

Example request:

```json
{
  "job_description": "We are looking for a Software Engineer with Python and FastAPI experience. AWS experience is preferred."
}
```

Example response:

```json
{
  "resume_id": 2,
  "filename": "Resume_Software.pdf",
  "job": {
    "job_title": "Software Engineer",
    "seniority_level": "unknown",
    "summary": "Software Engineer role requiring Python and FastAPI experience, with AWS experience preferred.",
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
  "matches": [
    {
      "requirement_name": "Python",
      "status": "matched",
      "evidence": "Resume evidence supporting Python experience.",
      "reason": "The resume provides direct or strong contextual evidence of Python usage."
    },
    {
      "requirement_name": "FastAPI",
      "status": "missing",
      "evidence": null,
      "reason": "The resume does not provide evidence of FastAPI experience."
    },
    {
      "requirement_name": "AWS",
      "status": "missing",
      "evidence": null,
      "reason": "The resume does not provide evidence of AWS experience."
    }
  ],
  "match_score": 42.86
}
```

## AI Analysis Design

CareerPilot uses structured AI outputs instead of relying on free-form model responses.

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

- Skill
- Experience
- Education
- Certification

Requirement importance is classified as:

- Required
- Preferred

### Resume Match Schema

```text
ResumeMatchResult
└── matches[]
    ├── requirement_name
    ├── status
    ├── evidence
    └── reason
```

Pydantic models and enums validate AI-generated data before it enters the scoring pipeline.

The job description remains the source of truth for scoring. Every job requirement must have a corresponding match result before a score can be calculated.

## Development Progress

### Backend Foundation

- [x] Set up Git and GitHub
- [x] Create Python virtual environment
- [x] Set up FastAPI and Uvicorn
- [x] Add Swagger API documentation
- [x] Configure environment variables for secrets

### Resume Pipeline

- [x] Upload PDF resumes
- [x] Read uploaded files as bytes
- [x] Extract text from PDFs
- [x] Create Resume ORM model
- [x] Set up SQLite database
- [x] Persist resume data
- [x] Generate resume IDs
- [x] Retrieve resumes by ID
- [x] Handle missing resumes with HTTP 404

### AI Pipeline

- [x] Integrate OpenAI API
- [x] Secure API credentials using environment variables
- [x] Define structured job requirement schemas
- [x] Add Pydantic validation
- [x] Extract structured requirements from job descriptions
- [x] Match resume evidence against individual job requirements
- [x] Classify requirements as matched, partial, or missing
- [x] Add evidence-based resume matching
- [x] Calculate deterministic weighted match scores
- [x] Connect the full analysis pipeline to the FastAPI endpoint
- [ ] Generate strengths and gaps
- [ ] Generate resume improvement recommendations
- [ ] Analyze candidate experience
- [ ] Improve AI matching consistency and evaluation

### Planned

- [ ] Resume-to-job strengths and gaps
- [ ] Resume improvement recommendations
- [ ] Candidate experience analysis
- [ ] Interview question generation
- [ ] Mock interview feedback
- [ ] User authentication
- [ ] Frontend application
- [ ] Production deployment

## Project Structure

```text
careerpilot/
├── backend/
│   ├── database/
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

CareerPilot is actively being developed.

The core resume-to-job matching and deterministic scoring pipeline is now functional.

The current focus is expanding the analysis with strengths, gaps, resume improvement recommendations, candidate experience insights, and improved AI evaluation consistency.