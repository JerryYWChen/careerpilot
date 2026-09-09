# CareerPilot

CareerPilot is an AI-powered career analysis and planning application that compares a resume against a job description, identifies strengths and requirement gaps, and turns those gaps into a prioritized career action plan.

Instead of asking a language model to directly generate an arbitrary match score or generic career advice, CareerPilot combines semantic AI reasoning with deterministic application logic:

- Structured LLM outputs
- Evidence-based resume matching
- Deterministic Python scoring
- Cross-gap career planning
- Deterministic plan validation
- Feedback-driven bounded retries
- Human-defined evaluation cases
- Automated planner tests
- FastAPI backend
- React + TypeScript frontend with end-to-end FastAPI integration

The project is currently under active development.

---

## What CareerPilot Does

CareerPilot is designed around five primary user-facing outputs:

```text
Job Title
    ↓
Match Score
    ↓
Strengths
    ↓
Gaps
    ↓
Career Action Plan
```

The goal is not only to tell a candidate how well a resume matches a role, but also to explain the evidence behind that assessment and provide realistic next steps for improving their fit.

---

# Current Features

## Resume & Job Analysis

- Upload PDF resumes
- Extract resume text with `pypdf`
- Store resume metadata and extracted text using SQLite and SQLAlchemy
- Retrieve stored resumes by ID
- Parse job descriptions into structured requirements using an LLM
- Validate structured AI outputs with Pydantic
- Match resume evidence against individual job requirements
- Classify requirements as `matched`, `partial`, or `missing`
- Track resume sections providing evidence
- Generate evidence-based explanations
- Calculate deterministic weighted match scores
- Convert requirement matches into strengths and gaps

## Career Action Planning

- Generate a prioritized action plan from multiple resume-to-job gaps
- Combine related gaps into shared actions when practical
- Reuse and extend existing candidate evidence when possible
- Represent dependencies between actions
- Distinguish short-term actionable gaps from long-term requirements
- Avoid treating projects as substitutes for unsupported years-of-experience requirements
- Validate generated plans with deterministic Python rules
- Feed validation errors back into the planner
- Retry invalid plans with bounded attempts

## Evaluation & Testing

- Human-defined matcher evaluation cases
- Repeated matcher consistency evaluation
- Evidence-source attribution evaluation
- Failure diagnostics for prompt and matching regressions
- Automated planner validation tests
- Automated feedback-retry tests
- Empty-gap behavior testing

## Frontend

CareerPilot now includes a functional React + TypeScript frontend connected to the FastAPI backend.

Current frontend capabilities:

- Upload a PDF resume
- Paste a job description using controlled form state
- Run the complete resume-to-job analysis workflow
- Display the extracted job title and deterministic match score
- Render matched strengths and partial/missing gaps
- Render the prioritized career action plan
- Disable repeated submissions while analysis is running
- Show loading feedback during analysis
- Handle upload and analysis failures with user-facing error feedback

The primary result interface currently presents:

```text
Job Title
Match Score
Strengths
Gaps
Career Action Plan
```

Detailed evidence and reasoning remain available in the backend response and can be exposed through expandable result details in a future frontend iteration.

---

# Architecture

CareerPilot separates semantic AI reasoning from deterministic application rules while using the React frontend as the user-facing entry point and result layer.

```text
Resume PDF + Job Description
            ↓
React + TypeScript Frontend
            ↓
FastAPI API
            ↓
Resume Processing + AI Analysis Pipeline
            ↓
Structured Analysis Response
            ↓
React Results UI
├── Job Title
├── Match Score
├── Strengths
├── Gaps
└── Career Action Plan
```

The backend analysis pipeline is:

```text
Resume PDF                          Job Description
    │                                     │
    ↓                                     ↓
Text Extraction                 Requirement Extraction
    │                                     │
    └─────────────────┬───────────────────┘
                      ↓
             Evidence-Based Matcher
                      ↓
               ResumeMatchResult
                      ↓
          ┌───────────┴───────────┐
          ↓                       ↓
 Deterministic Scoring       Match Analysis
          ↓                       │
     Match Score              ┌────┴────┐
                              ↓         ↓
                         Strengths     Gaps
                                       │
                                       ↓
                                 Career Planner
                                       ↓
                              Structured Action Plan
                                       ↓
                           Deterministic Validation
                                 ↙           ↘
                              Valid         Invalid
                                ↓              ↓
                              Return     Validation Error
                                               ↓
                                       Planner Feedback
                                               ↓
                                           Regenerate
```

The architecture follows a central principle:

> Use AI for semantic reasoning and generation; use deterministic code for rules that the application already knows.

---

# Resume Pipeline

```text
PDF Upload
    ↓
FastAPI UploadFile
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

The API validates that uploaded files are PDFs and rejects files that cannot produce usable text.

---

# Job Description Pipeline

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

Structured requirements include:

- Job title
- Seniority level
- Requirement category
- Required vs. preferred qualification
- Minimum years of experience when explicitly stated
- Job summary

---

# Resume Matching

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

The matcher performs semantic evidence analysis rather than simple keyword matching.

Evidence can come from:

```text
skills
experience
projects
research
education
certifications
```

The original job requirements remain the source of truth.

---

# Matching Logic

Each job requirement is classified into one of three states.

## Matched

The resume provides sufficient evidence supporting the requirement.

Examples include:

- Concrete use of a technology in a project or work experience
- Direct skill evidence supported by implementation evidence
- Strong contextual evidence that reliably establishes the capability

## Partial

Relevant evidence exists, but it does not fully satisfy the requirement.

Examples include:

- A skill appears with limited supporting evidence
- Related implementation evidence exists but does not fully establish the requirement
- Relevant experience exists but does not satisfy a stated duration
- The resume does not clearly establish the requested number of years

## Missing

The resume provides no reasonable evidence supporting the requirement.

CareerPilot is designed to avoid inferring unsupported skills from broadly related coursework, fields of study, or weakly related technologies.

---

# Evidence Sources

CareerPilot tracks where supporting evidence comes from separately from whether that evidence is sufficient.

For example:

```text
Python
├── status: matched
├── evidence_sources
│   ├── skills
│   └── projects
├── evidence
│   └── Python is listed and demonstrated through implementation.
└── reason
    └── Explicit skill evidence is supported by hands-on development.
```

This separates two questions:

```text
Where did the evidence come from?
```

from:

```text
Is the evidence sufficient to satisfy the requirement?
```

---

# Deterministic Match Score

CareerPilot does not ask the LLM to generate a match percentage.

The model produces structured requirement matches, while Python calculates the final score deterministically.

Current match values:

```text
matched = 1.0
partial = 0.8
missing = 0.0
```

Requirement weights:

```text
required  = 3
preferred = 1
```

Score:

```text
sum(match value × requirement weight)
───────────────────────────────────── × 100
        sum(requirement weights)
```

Every job requirement must have a corresponding match result. Missing results raise an error rather than silently changing the score.

The current scoring policy remains intentionally simple while real-world resume/job-description cases are collected for future calibration.

---

# Strengths and Gaps

Structured requirement matches are converted into product-level analysis using deterministic Python logic.

```text
MATCHED
   ↓
Strength

PARTIAL
   ↓
Gap
(existing evidence is insufficient)

MISSING
   ↓
Gap
(no supporting evidence)
```

A `Gap` retains its original match status so downstream systems can distinguish partial evidence from a genuinely missing capability.

---

# Career Action Planner

The Career Planner operates across the complete set of gaps rather than generating one isolated recommendation for every requirement.

This allows CareerPilot to recognize relationships such as:

```text
Docker ───────┐
              │
AWS ──────────┼──→ Deploy one containerized application
              │
Kubernetes ───┘
```

instead of automatically recommending three unrelated projects.

A generated plan uses the following structure:

```text
CareerActionPlan
└── actions[]
    ├── title
    ├── description
    ├── addresses_gaps[]
    ├── priority
    └── depends_on[]
```

This allows the planner to represent:

- One action addressing multiple gaps
- Multiple actions contributing to one gap
- Priority ordering
- Dependencies between actions
- Short-term and long-term improvements

The planner is instructed to prefer the smallest number of realistic actions that address the largest number of relevant gaps.

It also avoids introducing unnecessary infrastructure or implementation complexity when a simpler learning objective would be sufficient.

---

# Deterministic Plan Validation

A valid Pydantic object is not automatically considered a valid career plan.

Pydantic validates the output structure, while deterministic Python logic validates application-level planning constraints.

Current validation rules include:

```text
✓ Action titles must be unique
✓ Priorities must be sequential
✓ addresses_gaps must reference real input gaps
✓ depends_on must reference real actions
✓ Every input gap must be addressed
✓ Dependency graphs must not contain cycles
```

For example, this is structurally valid JSON:

```text
addresses_gaps = ["Docker (missing)"]
```

but it is rejected if the original gap is named:

```text
Docker
```

This prevents generated plans from silently modifying application identifiers.

---

# Feedback-Driven Plan Repair

When a generated plan fails deterministic validation, CareerPilot uses the validation error as feedback for another planning attempt.

```text
Generate Plan
     ↓
Validate
     ↓
   FAIL
     ↓
Validation Error
     ↓
Planner Feedback
     ↓
Regenerate
     ↓
Validate Again
```

For example:

```text
Unknown gap 'Docker (missing)' in action 'Learn Docker'.
```

is passed back to the planner so the next attempt can repair the exact validation failure.

Retries are bounded to prevent uncontrolled generation loops.

The current default is:

```text
Maximum attempts: 3
```

If all attempts fail, the service raises an explicit error instead of returning an invalid plan.

If there are no gaps, the planner immediately returns an empty action plan without making an unnecessary LLM call.

---

# Planner Testing

Planner orchestration and validation behavior are covered with automated `pytest` tests.

Current tests verify:

```text
✓ Valid plans return without retry
✓ Invalid plans trigger regeneration
✓ Validation feedback reaches the next attempt
✓ Maximum retry attempts are enforced
✓ Empty gaps return an empty plan without generation
```

Current planner test result:

```text
5 / 5 tests passing
```

The tests mock LLM generation so planner control flow can be tested deterministically without depending on model behavior.

---

# AI Matching Evaluation

CareerPilot includes a repeatable evaluation suite for testing resume matching behavior against human-defined expected results.

Each evaluation case contains expected requirement statuses and evidence sources.

The evaluator tests:

- Match classification
- Evidence-source attribution
- Missing requirement detection
- Contextual evidence boundaries
- Repeated model consistency
- Prompt regressions

Failures include diagnostic information such as:

```text
Requirement
Expected status
Actual status
Expected evidence sources
Actual evidence sources
Selected evidence
Model reasoning
```

This makes failures inspectable before prompts, schemas, or business rules are changed.

## Matcher v1 Baseline

The current frozen matcher baseline is:

```text
Active evaluation cases: 9
Runs per case: 3
Total evaluation runs: 27
Passing runs: 25
Overall run accuracy: 92.6%
```

Known contextual-evidence boundary cases are intentionally retained rather than removed or overfit through prompt changes.

This result measures performance only on the current human-defined evaluation suite and should not be interpreted as general accuracy across arbitrary resumes and job descriptions.

Real-world job descriptions are now being used to identify additional cases involving compound requirements, evidence-classification consistency, and score calibration.

---

# Experimental Agent Workflow

Earlier versions of CareerPilot explored per-gap recommendation generation using LangGraph.

The workflow includes:

```text
Gap
 ↓
Deterministic Routing
 ├── PARTIAL → Resume Improvement
 └── MISSING → Skill Development
 ↓
Recommendation
 ↓
Reviewer
 ↓
Feedback
 ↓
Bounded Retry
```

The workflow uses shared state to coordinate generation, review, feedback, and retry behavior.

This implementation remains in the codebase as an experimental agent architecture.

The primary product flow has since evolved toward cross-gap planning, where one coordinated action can address multiple related requirements.

---

# API

## Upload Resume

```text
POST /resume
```

Uploads a PDF resume, extracts its text, stores it, and returns a unique resume ID.

Example response:

```json
{
  "resume_id": 1,
  "filename": "Resume_AI.pdf",
  "size": 133981,
  "text_preview": "..."
}
```

---

## Retrieve Resume

```text
GET /resume/{resume_id}
```

Retrieves metadata for a stored resume.

A nonexistent resume returns:

```text
404 Not Found
```

---

## Analyze Resume

```text
POST /resume/{resume_id}/analyze
```

The endpoint currently:

1. Retrieves the stored resume
2. Extracts structured job requirements
3. Matches resume evidence against each requirement
4. Calculates a deterministic match score
5. Builds strengths and gaps
6. Generates resume highlights
7. Generates a cross-gap career action plan
8. Validates the action plan
9. Retries invalid plans using validation feedback
10. Returns the structured analysis

Example request:

```json
{
  "job_description": "AI Engineer role requiring Python, FastAPI, LLM application development, AWS, Docker, Kubernetes, and three years of software engineering experience."
}
```

Simplified response structure:

```json
{
  "resume_id": 3,
  "filename": "Resume_AI.pdf",
  "job": {
    "job_title": "AI Engineer",
    "seniority_level": "mid",
    "summary": "...",
    "requirements": []
  },
  "match_score": 54.29,
  "strengths": [],
  "gaps": [],
  "resume_highlights": {
    "highlights": []
  },
  "career_action_plan": {
    "actions": [
      {
        "title": "...",
        "description": "...",
        "addresses_gaps": [],
        "priority": 1,
        "depends_on": []
      }
    ]
  }
}
```

The primary product interface focuses on:

```text
Job Title
Match Score
Strengths
Gaps
Career Action Plan
```

Resume highlights are retained as a backend capability but are not currently a primary result-page section.

---

# Core Schemas

## Job Requirements

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

## Resume Match

```text
ResumeMatchResult
└── matches[]
    ├── requirement_name
    ├── status
    ├── evidence
    ├── evidence_sources[]
    └── reason
```

## Match Analysis

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

## Career Action Plan

```text
CareerActionPlan
└── actions[]
    ├── title
    ├── description
    ├── addresses_gaps[]
    ├── priority
    └── depends_on[]
```

---

# Tech Stack

## Frontend

- React
- TypeScript
- Vite

## Backend

- Python
- FastAPI
- Uvicorn
- Pydantic

## AI & Agentic Systems

- OpenAI API
- Structured Outputs
- Evidence-based semantic matching
- Cross-gap planning
- LangGraph
- Feedback-driven generation and repair

## Database

- SQLite
- SQLAlchemy

## Document Processing

- pypdf

## Testing & Evaluation

- pytest
- Human-defined matching ground truth
- Repeated matcher consistency evaluation
- Evidence-source evaluation
- Deterministic planner tests
- Failure diagnostics

---

# Project Structure

```text
careerpilot/
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── state.py
│   │   ├── nodes.py
│   │   └── graph.py
│   │
│   ├── database/
│   │   └── database.py
│   │
│   ├── evals/
│   │   ├── matching_cases.py
│   │   └── run_matching_eval.py
│   │
│   ├── models/
│   │   ├── resume.py
│   │   ├── analysis.py
│   │   └── api.py
│   │
│   ├── services/
│   │   ├── resume_service.py
│   │   ├── ai_service.py
│   │   ├── scoring_service.py
│   │   ├── agent_service.py
│   │   └── planner_service.py
│   │
│   └── main.py
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── App.css
│   │   ├── App.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── tests/
│   └── test_planner_service.py
│
├── test_agent.py
├── .gitignore
└── README.md
```

Local secrets such as API credentials are stored in `.env`, which is excluded from Git.

---

# Development Progress

## Backend Foundation

- [x] FastAPI backend
- [x] Swagger API documentation
- [x] Environment-based secret configuration
- [x] SQLite persistence
- [x] SQLAlchemy ORM
- [x] Pydantic request and response models

## Resume Pipeline

- [x] PDF resume upload
- [x] PDF text extraction
- [x] Resume persistence
- [x] Resume ID generation
- [x] Resume retrieval
- [x] PDF validation
- [x] Missing-resume handling

## AI Matching Pipeline

- [x] Structured job requirement extraction
- [x] Evidence-based resume matching
- [x] Matched / partial / missing classification
- [x] Evidence-source tracking
- [x] Evidence-based explanations
- [x] Deterministic weighted scoring
- [x] Strength and gap generation
- [x] Establish Matcher v1 baseline

## Career Planning

- [x] Cross-gap career planning
- [x] Multi-gap actions
- [x] Action prioritization
- [x] Action dependencies
- [x] Structured `CareerActionPlan`
- [x] Deterministic plan validation
- [x] Unknown-gap validation
- [x] Dependency validation
- [x] Complete gap coverage validation
- [x] Circular dependency detection
- [x] Feedback-driven retry
- [x] Bounded generation attempts
- [x] Empty-gap optimization
- [x] End-to-end API integration

## Testing & Evaluation

- [x] Human-defined matcher evaluation cases
- [x] Status evaluation
- [x] Evidence-source evaluation
- [x] Repeated consistency evaluation
- [x] Failure diagnostics
- [x] Matcher v1 baseline: 25/27 passing runs
- [x] Planner automated tests: 5/5 passing
- [x] Planner retry behavior tests
- [x] Validation-feedback propagation test
- [ ] Expand matcher coverage with real-world job descriptions
- [ ] Review requirement extraction for compound AND/OR requirements
- [ ] Investigate evidence-classification consistency for direct skills such as SQL and PyTorch
- [ ] Calibrate match scoring against real resume/JD cases
- [ ] Add planner-quality evaluation cases

## Frontend

- [x] Initialize React + TypeScript + Vite application
- [x] Remove default Vite application shell
- [x] Add initial CareerPilot application shell
- [x] Add controlled job-description input
- [x] Add PDF resume upload interface
- [x] Connect React frontend to FastAPI
- [x] Add sequential resume-upload and analysis requests
- [x] Add loading state and duplicate-submission protection
- [x] Add frontend error handling and user-facing failure feedback
- [x] Display job title and match score
- [x] Render strengths
- [x] Render partial and missing gaps
- [x] Render prioritized career action plan
- [ ] Improve result-page layout and visual hierarchy
- [ ] Add expandable strength and gap evidence
- [ ] Add expandable action-plan details

## Future

- [ ] Persist completed analyses
- [ ] Add analysis history
- [ ] Add frontend/API integration tests
- [ ] Improve application logging and error handling
- [ ] Add interview preparation workflows
- [ ] Add user authentication
- [ ] Containerize application
- [ ] Deploy to production

---

# Design Principles

**Structured outputs over free-form parsing**

Important AI outputs are validated with Pydantic whenever possible.

**AI for semantic reasoning, Python for deterministic rules**

LLMs interpret resume evidence and generate plans. Scoring, validation, dependency checks, retry limits, and other known business rules remain deterministic.

**Evidence before claims**

CareerPilot should never encourage candidates to fabricate experience. Missing capabilities should result in learning, project, or long-term experience actions rather than unsupported resume claims.

**Plan across gaps, not only within gaps**

Related requirements should be considered together. One coherent project may be more useful than several isolated recommendations.

**Validate before trusting generated plans**

A response satisfying the Pydantic schema may still violate product rules. Generated plans therefore pass through deterministic semantic validation.

**Feedback before blind retry**

When generation fails validation, the next attempt receives the actual validation error instead of blindly repeating the same prompt.

**Evaluation before prompt overfitting**

Known model inconsistencies are measured through regression cases rather than immediately changing prompts to fit individual examples.

**Bounded autonomy**

AI retries are explicitly limited to prevent uncontrolled loops.

---

# Status

CareerPilot now has a functional end-to-end MVP spanning the React frontend and FastAPI backend.

```text
Upload Resume + Paste Job Description
                ↓
React Frontend
                ↓
Upload & Extract Resume
                ↓
Analyze Job Description
                ↓
Match Resume Evidence
                ↓
Calculate Deterministic Score
                ↓
Identify Strengths & Gaps
                ↓
Generate Cross-Gap Career Plan
                ↓
Validate / Repair Plan
                ↓
Return Structured API Response
                ↓
React Results UI
```

Current product output:

```text
Job Title
Match Score
Strengths
Gaps
Career Action Plan
```

Matcher v1 remains frozen while real-world job descriptions are used to identify requirement-extraction, evidence-classification, and score-calibration cases.

Current regression baseline:

```text
25 / 27 passing matcher runs
92.6% on the current evaluation suite
```

Planner control-flow tests:

```text
5 / 5 passing
```

The next development phase will focus on:

- Evaluating matcher behavior on real-world job descriptions
- Improving requirement extraction and evidence-classification consistency
- Calibrating match scoring without overfitting individual examples
- Improving frontend layout and result presentation
- Adding expandable evidence, reasoning, and action-plan details