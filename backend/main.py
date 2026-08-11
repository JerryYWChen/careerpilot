from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database.database import Base, engine, get_db
from backend.models.resume import Resume
from backend.services.resume_service import extract_text_from_pdf



class AnalyzeRequest(BaseModel):
    job_description: str
    
app = FastAPI()
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return{"message": "Hello CareerPilot!"}

@app.get("/resume/{resume_id}")
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if resume is None:
        raise HTTPException(
            status_code=404,
            detail="Resume not found"
        )

    return {
        "resume_id": resume.id,
        "filename": resume.filename,
        "created_at": resume.created_at
    }

@app.post("/resume")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    text = extract_text_from_pdf(content)

    resume = Resume(
        filename=file.filename,
        file_path=None,
        extracted_text=text
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    return {
        "resume_id": resume.id,
        "filename": resume.filename,
        "size": len(content),
        "text_preview": resume.extracted_text[:500]
    }

@app.post("/resume/{resume_id}/analyze")
async def analyze_resume(resume_id: int, request: AnalyzeRequest, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if resume is None:
        raise HTTPException(
            status_code=404,
            detail="Resume not found"
        )
    
    return {
        "resume_id": resume_id,
        "filename": resume.filename,
        "resume_preview": resume.extracted_text[:200],
        "job_description": request.job_description
    }