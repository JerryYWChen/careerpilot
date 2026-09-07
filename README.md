# CareerPilot

CareerPilot is an AI-powered career assistant that analyzes resumes against job descriptions, identifies strengths and requirement gaps, and generates grounded, actionable career recommendations.

Rather than asking a language model to directly produce an arbitrary match score or generic advice, CareerPilot combines:

- Structured LLM outputs
- Evidence-based resume matching
- Deterministic Python scoring
- Human-defined evaluation cases
- LangGraph-based agentic workflows
- Specialized recommendation agents
- LLM review and reflection
- Feedback-driven bounded retries

The project is currently under active development.

---

## Current Features

### Resume & Job Analysis

- Upload resumes as PDF files
- Extract resume text with `pypdf`
- Store resume metadata and extracted text using SQLite and SQLAlchemy
- Retrieve stored resumes by ID
- Parse job descriptions into structured requirements using AI
- Validate AI-generated structured data with Pydantic
- Match resume evidence against individual job requirements
- Support direct and contextual evidence
- Classify requirements as `matched`, `partial`, or `missing`
- Track resume sections providing evidence for each requirement
- Generate evidence-based explanations for match decisions
- Calculate deterministic weighted resume-to-job match scores
- Identify strengths and requirement gaps

### Agentic Career Recommendations

- Route different gap types to specialized recommendation workflows
- Send partial matches to a Resume Improvement agent
- Send missing requirements to a Skill Development agent
- Generate grounded, actionable recommendations
- Review generated recommendations with an LLM reviewer
- Detect recommendations that are vague or unsupported
- Store reviewer feedback in shared agent state
- Retry failed recommendations using reviewer feedback
- Limit retries to prevent uncontrolled agent loops
- Process multiple gaps through the agent workflow
- Return reviewed agent actions through the analysis API

### AI Evaluation

- Evaluate matcher behavior against human-defined expected results
- Evaluate evidence-source attribution
- Run repeated evaluation cases to measure consistency
- Detect prompt and matching regressions
- Log detailed failure information for debugging
- Preserve difficult contextual-evidence boundary cases

### API

- REST API built with FastAPI
- Pydantic request and response schemas
- Interactive API testing through Swagger UI
- End-to-end resume analysis through `/resume/{resume_id}/analyze`

---

# Architecture

CareerPilot separates semantic AI reasoning from deterministic application logic and agent orchestration.

```text
Resume PDF                     Job Description
    │                                │
    ↓                                ↓
Text Extraction              Requirement Extraction
    │                                │
    └──────────────┬─────────────────┘
                   ↓
          Evidence-Based Matcher
                   ↓
           ResumeMatchResult
                   ↓
        ┌──────────┴──────────┐
        ↓                     ↓
Deterministic Scoring    Match Analysis
        ↓                     │
   Match Score          ┌─────┴─────┐
                        ↓           ↓
                    Strengths      Gaps
                                      │
                                      ↓
                               Agent Service
                                      ↓
                              LangGraph Workflow
                                      ↓
                                Agent Actions
```

---

## Resume Pipeline

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

---

## Job Description Pipeline

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

## Resume Matching Pipeline

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

The language model performs semantic evidence analysis rather than simple keyword matching.

Evidence may come from:

- Skills
- Work experience
- Projects
- Research
- Education
- Certifications
- Related technologies and frameworks
- Concrete implementation details

The matcher considers the total strength of available evidence and supports both direct and contextual evidence.

---

# Matching Logic

Each job requirement is classified into one of three states.

## Matched

The resume provides direct evidence or sufficiently strong contextual evidence supporting the requirement.

Examples:

- Concrete use of a technology in a project or work experience
- Multiple related technologies combined with implementation evidence
- Framework and implementation context that reliably establishes a broader technical capability

## Partial

Relevant evidence exists, but it is incomplete, indirect, or insufficient to fully satisfy the requirement.

Examples:

- A skill appears only in the Skills section
- Related evidence exists but does not reliably establish the exact requirement
- Relevant experience exists but does not satisfy a required duration
- The resume does not clearly establish the requested number of years

## Missing

The resume provides no reasonable evidence supporting the requirement.

CareerPilot is instructed not to infer skills merely from broadly related coursework, fields of study, or weakly related technologies.

---

# Evidence Sources

CareerPilot tracks where supporting evidence comes from separately from whether that evidence is sufficient.

Current evidence sources:

```text
skills
experience
projects
research
education
certifications
```

For example:

```text
Python
├── status: matched
├── evidence_sources
│   ├── skills
│   └── experience
├── evidence
│   └── Python is listed and demonstrated in backend development.
└── reason
    └── Direct skill evidence is supported by implementation experience.
```

This separates two different questions:

```text
Where did the evidence come from?
```

from:

```text
Is that evidence sufficient to satisfy the requirement?
```

---

# Deterministic Match Score

CareerPilot does not ask the LLM to generate a match percentage.

The model produces structured requirement matches, and Python calculates the final score deterministically.

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

The original job requirements remain the source of truth.

Every requirement must have a corresponding match result. Missing results raise an error instead of silently increasing the score.

---

# Strengths and Gaps

Structured matches are converted into user-facing analysis using deterministic Python logic.

```text
MATCHED
   ↓
Strength

PARTIAL
   ↓
Gap
(existing evidence needs strengthening)

MISSING
   ↓
Gap
(no supporting evidence)
```

A `Gap` retains its status so downstream systems can distinguish between:

- Evidence that already exists but needs stronger presentation
- A genuinely unsupported requirement

This distinction is also used by the agentic recommendation workflow.

---

# Agentic Recommendation Workflow

CareerPilot uses LangGraph to turn identified gaps into reviewed, actionable next steps.

Each gap is processed independently through a stateful workflow.

```text
                     ┌── Resume Improvement ──┐
                     │       PARTIAL           │
Gap → Route Gap ─────┤                         ├──→ Reviewer
                     │       MISSING           │       │
                     └── Skill Development ────┘       ↓
                                                    Pass?
                                                   ↙     ↘
                                                 Yes      No
                                                  ↓        ↓
                                                 END    Feedback
                                                           ↓
                                                      Retry Count
                                                           ↓
                                                       Regenerate
```

## Gap Routing

Routing is deterministic.

```text
PARTIAL
    ↓
resume_improvement

MISSING
    ↓
skill_development
```

The LLM is not used for routing when the business rule is already known.

### Resume Improvement Agent

Used for `partial` requirements.

The agent focuses on improving how existing evidence is presented without inventing new experience.

For example:

```text
AWS is listed in Skills
but has weak supporting evidence
        ↓
Resume Improvement
        ↓
Clarify real AWS usage in a project or experience,
if such evidence actually exists
```

### Skill Development Agent

Used for `missing` requirements.

Instead of telling the candidate to add an unsupported skill to the resume, the agent proposes a concrete way to build real evidence.

For example:

```text
Kubernetes = missing
        ↓
Skill Development
        ↓
Build a small Kubernetes deployment
        ↓
Document it as portfolio evidence
```

---

# Review and Reflection

Generated actions are evaluated by a separate reviewer.

The reviewer checks two primary properties:

### Grounded

The recommendation must not invent or assume:

- Skills
- Experience
- Projects
- Achievements
- Qualifications

### Actionable

The recommendation must provide a specific next action rather than vague advice.

The reviewer returns structured output:

```text
RecommendationReview
├── passed
└── feedback
```

The result is stored in the shared LangGraph state.

---

## Feedback-Driven Retry

If a recommendation fails review, CareerPilot does not simply repeat the same generation step.

Reviewer feedback is stored in agent state and passed back to the appropriate generator.

```text
Generate
    ↓
Review
    ↓
FAIL
    ↓
Reviewer Feedback
    ↓
Agent State
    ↓
Retry
    ↓
Generator reads feedback
    ↓
Revised Recommendation
    ↓
Review Again
```

Retries are bounded to prevent uncontrolled loops.

Current maximum:

```text
2 retries
```

This means one initial generation plus at most two revisions.

---

# Agent State

LangGraph nodes communicate through a shared state.

```text
CareerAgentState
├── current_gap
├── action_type
├── recommendation
├── review_passed
├── review_feedback
└── retry_count
```

The state allows different nodes to share workflow progress without tightly coupling their implementations.

For example:

```text
Reviewer
    ↓
review_feedback stored in State
    ↓
Retry routing
    ↓
Generator reads review_feedback
```

---

# Agent Service Layer

The LangGraph workflow operates on one gap at a time.

CareerPilot's agent service adapts this workflow to real resume analyses containing multiple gaps.

```text
MatchAnalysis.gaps
        ↓
generate_agent_actions()
        ↓
┌─────────────────────────────┐
│ Gap 1 → Career Agent        │
│ Gap 2 → Career Agent        │
│ Gap 3 → Career Agent        │
└─────────────────────────────┘
        ↓
list[AgentAction]
```

Each gap receives an independent agent state so retries and reviewer feedback do not leak between requirements.

An `AgentAction` contains:

```text
AgentAction
├── gap
├── action_type
├── recommendation
├── review_passed
└── retry_count
```

---

# AI Recommendations

CareerPilot currently also retains its original high-level recommendation generator.

It produces:

```text
Recommendations
├── highlight[]
└── strengthen[]
```

`highlight` focuses on making existing strengths more visible.

`strengthen` focuses on partial and missing requirements.

The newer `agent_actions` workflow adds requirement-level routing, review, reflection, and retry.

These systems are currently kept separate while the agentic recommendation architecture is evaluated and refined.

---

# AI Matching Evaluation

CareerPilot includes a repeatable evaluation suite for testing resume matching behavior against human-defined ground truth.

Each case contains:

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

The evaluator tests:

- Match classification
- Evidence-source attribution
- Missing requirement detection
- Contextual evidence boundaries
- Repeated model consistency
- Prompt regressions

When a run fails, diagnostics can include:

```text
Requirement
Expected status
Actual status
Expected evidence sources
Actual evidence sources
Selected evidence
Model reasoning
```

This makes failures inspectable before prompts, schemas, or product rules are changed.

---

## Current Evaluation Coverage

The active suite includes nine cases covering:

- Mixed matched, partial, and missing evidence
- Minimum years of experience
- Strong direct implementation evidence
- Completely missing evidence
- Insufficient contextual evidence
- Framework-to-language contextual evidence
- Backend framework-to-language evidence
- Concrete tools supporting broader concepts
- Explicit skills combined with contextual evidence

Cases are executed repeatedly to measure consistency.

### Current Matcher v1 Baseline

```text
Active evaluation cases: 9
Runs per case: 3
Total evaluation runs: 27
Passing runs: 25
Overall run accuracy: 92.6%
```

The remaining failures are retained as known contextual-evidence boundary cases rather than being removed or overfit through prompt changes.

This result represents performance on the current human-defined evaluation suite only. It should not be interpreted as general accuracy across arbitrary resumes and job descriptions.

---

# Tech Stack

## Backend

- Python
- FastAPI
- Uvicorn
- Pydantic

## Agent Orchestration

- LangGraph
- Stateful workflow routing
- Conditional edges
- LLM review and reflection
- Feedback-driven bounded retries

## AI

- OpenAI API
- Structured Outputs
- Pydantic-based response validation
- Evidence-based semantic matching
- Specialized recommendation generation

## Database

- SQLite
- SQLAlchemy

## Document Processing

- pypdf

## Evaluation

- Human-defined ground truth
- Requirement classification evaluation
- Evidence-source evaluation
- Repeated consistency testing
- Failure diagnostics

## Frontend

- TBD

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

Runs the complete CareerPilot analysis and agent workflow.

The endpoint:

1. Retrieves the stored resume
2. Extracts structured job requirements
3. Matches resume evidence against every requirement
4. Classifies each requirement
5. Calculates a deterministic match score
6. Builds strengths and gaps
7. Sends gaps through the LangGraph agent workflow
8. Generates specialized actions
9. Reviews recommendations
10. Retries failed recommendations with reviewer feedback
11. Returns the complete structured analysis

Example request:

```json
{
  "job_description": "AI Engineer role requiring Python, FastAPI, LLM application development, AWS, Docker, Kubernetes, and three years of software engineering experience."
}
```

Example response structure:

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
  "recommendations": {
    "highlight": [],
    "strengthen": []
  },
  "agent_actions": [
    {
      "gap": "Kubernetes",
      "action_type": "skill_development",
      "recommendation": "Build and deploy a small containerized application to a local Kubernetes cluster...",
      "review_passed": true,
      "retry_count": 0
    },
    {
      "gap": "Software engineering experience",
      "action_type": "resume_improvement",
      "recommendation": "Clarify the dates and implementation responsibilities of existing software projects...",
      "review_passed": true,
      "retry_count": 0
    }
  ]
}
```

---

# Core Schemas

## Job Requirement

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

## Agent Review

```text
RecommendationReview
├── passed
└── feedback
```

## Agent Action

```text
AgentAction
├── gap
├── action_type
├── recommendation
├── review_passed
└── retry_count
```

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
│   │   └── agent_service.py
│   │
│   └── main.py
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
- [x] Direct and contextual evidence support
- [x] Matched / partial / missing classification
- [x] Evidence-source tracking
- [x] Evidence-based explanations
- [x] Deterministic weighted scoring
- [x] Strength and gap generation
- [x] Grounded high-level recommendations

## Agentic Workflow

- [x] Add LangGraph
- [x] Define shared CareerAgentState
- [x] Add deterministic gap routing
- [x] Add Resume Improvement agent
- [x] Add Skill Development agent
- [x] Add structured recommendation reviewer
- [x] Store reviewer feedback in agent state
- [x] Add conditional retry routing
- [x] Add bounded retry count
- [x] Add feedback-driven recommendation revision
- [x] Process multiple gaps through agent service
- [x] Expose agent actions through `/analyze`
- [x] Complete end-to-end API integration test

## AI Evaluation

- [x] Human-defined matching evaluation cases
- [x] Status evaluation
- [x] Evidence-source evaluation
- [x] Repeated consistency evaluation
- [x] Failure diagnostics
- [x] Establish Matcher v1 baseline
- [x] Preserve known contextual boundary cases
- [ ] Expand coverage with real-world failures
- [ ] Track evaluation results across matcher versions
- [ ] Add evaluation coverage for agent recommendations

## Planned

- [ ] Define final relationship between high-level recommendations and agent actions
- [ ] Add automated tests for agent routing and retry behavior
- [ ] Add agent recommendation evaluation
- [ ] Improve request validation and application logging
- [ ] Add recommendation prioritization
- [ ] Generate interview questions from job gaps
- [ ] Add mock interview feedback
- [ ] Build frontend application
- [ ] Add user authentication
- [ ] Deploy to production

---

# Design Principles

CareerPilot follows several design principles:

**Structured outputs over free-form parsing**  
Important AI outputs are validated with Pydantic whenever possible.

**AI for semantic reasoning, Python for deterministic rules**  
LLMs interpret evidence and generate recommendations. Scoring, routing, retry limits, and other known business rules remain deterministic.

**Evidence before claims**  
CareerPilot should never encourage candidates to fabricate experience. Missing skills should result in learning or project actions rather than unsupported resume claims.

**Evaluation before prompt overfitting**  
Known model inconsistencies are measured through regression cases instead of immediately modifying prompts to fit individual examples.

**Agent state for workflow coordination**  
Generation, review, feedback, routing, and retries communicate through explicit shared state.

**Bounded autonomy**  
Agent retries are limited and controlled rather than allowing unconstrained loops.

---

# Status

CareerPilot's core backend and agentic resume-analysis workflow are functional end-to-end.

The system can currently:

```text
Upload Resume
    ↓
Extract & Store Resume
    ↓
Analyze Job Description
    ↓
Match Resume Evidence
    ↓
Calculate Deterministic Score
    ↓
Identify Strengths & Gaps
    ↓
Route Gaps to Specialized Agents
    ↓
Generate Actions
    ↓
Review Recommendations
    ↓
Reflect & Retry When Needed
    ↓
Return Structured API Response
```

Matcher v1 is currently frozen while the surrounding product architecture is developed. Its current regression baseline is **25/27 passing runs (92.6%)** on nine human-defined evaluation cases executed three times each.

The next development focus is refining the relationship between the original recommendation system and the newer agentic actions, adding agent-level evaluation and automated workflow tests, and continuing toward a user-facing frontend.