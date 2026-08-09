from fastapi import FastAPI, UploadFile, File, Depends
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
async def analyze_resume(resume_id: int, request: AnalyzeRequest):
    return {
        "resume_id": resume_id,
        "job_description": request.job_description,
        "message": "Resume analysis started successfully."
    }