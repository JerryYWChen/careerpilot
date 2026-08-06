from fastapi import FastAPI, UploadFile, File

app = FastAPI()

@app.get("/")
def root():
    return{"message": "Hello CareerPilot!"}

@app.post("/resume")
def upload_resume(file: UploadFile = File(...)):
    return{"filename": file.filename}