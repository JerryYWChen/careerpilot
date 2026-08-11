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
- Validate AI-generated structured data with Pydantic
- REST API built with FastAPI
- Interactive API testing with Swagger UI

## Current Architecture

CareerPilot currently follows two main backend pipelines.

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
FastAPI
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

If the resume does not exist, the API returns `404 Not Found`.

### Analyze Resume

`POST /resume/{resume_id}/analyze`

Accepts a job description for a stored resume and retrieves both the resume text and job description for analysis.

Full resume-to-job matching is currently under development.

Example request:

```json
{
  "job_description": "We are looking for a Software Engineer with experience in Python, FastAPI, SQL, REST APIs, and cloud technologies."
}
```

## AI Analysis Design

CareerPilot uses structured AI outputs instead of relying on free-form model responses.

Job descriptions are converted into structured requirements containing:

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

Pydantic models and enums are used to validate AI-generated data before it enters the matching pipeline.

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
- [ ] Match resume evidence against individual job requirements
- [ ] Calculate deterministic match scores
- [ ] Generate strengths and gaps
- [ ] Generate resume improvement recommendations
- [ ] Analyze candidate experience

### Planned

- [ ] Resume-to-job matching feedback
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
│   │   └── ai_service.py
│   └── main.py
├── .env
├── .gitignore
└── README.md
```

> `.env` contains local secrets such as API credentials and is excluded from Git.

## Status

CareerPilot is actively being developed.

The current focus is building the resume-to-job requirement matching and scoring pipeline.