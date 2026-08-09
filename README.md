# CareerPilot

CareerPilot is an AI-powered career assistant designed to help users analyze their resumes against job descriptions and prepare for interviews.

The project is currently under active development.

## Current Features

- Upload resumes as PDF files
- Extract text from uploaded PDFs
- Store resume metadata and extracted text using SQLite
- Generate unique resume IDs for uploaded resumes
- REST API built with FastAPI
- Interactive API testing with Swagger UI

## Current Architecture

CareerPilot currently follows this backend flow:

```text
PDF Upload
    ↓
FastAPI
    ↓
UploadFile
    ↓
PDF Parsing
    ↓
Extracted Text
    ↓
SQLAlchemy ORM
    ↓
SQLite Database
```

## Tech Stack

### Backend

- Python
- FastAPI
- Uvicorn

### Database

- SQLite
- SQLAlchemy

### Document Processing

- pypdf

### AI

- OpenAI API *(planned)*

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

### Analyze Resume

`POST /resume/{resume_id}/analyze`

Accepts a job description for a specific resume.

AI-powered analysis is currently under development.

Example request:

```json
{
  "job_description": "We are looking for an AI Engineer..."
}
```

## Development Progress

### Backend Foundation

- [x] Set up Git and GitHub
- [x] Create Python virtual environment
- [x] Set up FastAPI and Uvicorn
- [x] Add Swagger API documentation

### Resume Pipeline

- [x] Upload PDF resumes
- [x] Read uploaded files as bytes
- [x] Extract text from PDFs
- [x] Create Resume ORM model
- [x] Set up SQLite database
- [x] Persist resume data
- [x] Generate resume IDs
- [ ] Retrieve resumes by ID
- [ ] Analyze resumes against job descriptions

### Planned

- [ ] OpenAI integration
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
│   ├── services/
│   └── main.py
├── .gitignore
└── README.md
```

## Status

CareerPilot is actively being developed.

The current focus is building the resume processing and analysis pipeline.