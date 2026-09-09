import { useState } from 'react'
import './App.css'
type AnalysisResult = {
  match_score: number
  job: {
    job_title: string
  }
  strengths: {
    area: string
    evidence: string
    reason: string
  }[]
  gaps: {
    area: string
    status: 'partial' | 'missing'
    evidence: string | null
    reason: string
  }[]
  career_action_plan: {
    actions: {
      title: string
      description: string
      addresses_gaps: string[]
      priority: number
      depends_on: string[]
    }[]
  }
}
function App() {
  const [jobDescription, setJobDescription] = useState('')
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const handleAnalyze = async () => {
    if (!resumeFile || !jobDescription.trim()) {
      return
    }

    setIsAnalyzing(true)
    setError(null)
    setAnalysis(null)
    try {
      const formData = new FormData()
      formData.append('file', resumeFile)

      const uploadResponse = await fetch('http://127.0.0.1:8000/resume', {
        method: 'POST',
        body: formData,
      })
      if (!uploadResponse.ok) {
        throw new Error('Resume upload failed')
      }

      const uploadData = await uploadResponse.json()

      console.log('Upload:', uploadData)

      const analyzeResponse = await fetch(
        `http://127.0.0.1:8000/resume/${uploadData.resume_id}/analyze`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            job_description: jobDescription,
          }),
        },
      )
      if (!analyzeResponse.ok) {
        throw new Error('Analysis failed')
      }
      const analyzeData = await analyzeResponse.json()
      console.log('Analysis:', analyzeData)
      setAnalysis(analyzeData)
    } catch (error) {
      console.error(error)
      setError('Analysis failed. Please try again.')
    } finally {
      setIsAnalyzing(false)
    }
  }
  return (
    <main>
      <h1>CareerPilot</h1>
      <p>Analyze your resume against a job description.</p>

      <label htmlFor="resume">
        Resume
      </label>

      <input
        id="resume"
        type="file"
        accept=".pdf"
        onChange={(event) => {
          const file = event.target.files?.[0] ?? null
          setResumeFile(file)
        }}
      />

      {resumeFile && (
        <p>Selected: {resumeFile.name}</p>
      )}

      <label htmlFor="job-description">
        Job Description
      </label>

      <textarea
        id="job-description"
        value={jobDescription}
        onChange={(event) => setJobDescription(event.target.value)}
        placeholder="Paste the job description here..."
        rows={10}
      />

      <button
        disabled={
          !resumeFile ||
          !jobDescription.trim() ||
          isAnalyzing
        }
        onClick={handleAnalyze}
      >
        {isAnalyzing ? 'Analyzing...' : 'Analyze'}
      </button>
      {error && (
        <p>{error}</p>
      )}

      {analysis && (
        <section>
          <h2>{analysis.job.job_title}</h2>

          <p>{analysis.match_score}% Match</p>

          <h3>Strengths</h3>

          {analysis.strengths.map((strength) => (
            <p key={strength.area}>
              ✓ {strength.area}
            </p>
          ))}
          <h3>Gaps</h3>

          {analysis.gaps.map((gap) => (
            <p key={gap.area}>
              {gap.status === 'missing' ? '✕' : '△'} {gap.area} — {gap.status}
            </p>
          ))}

          <h3>Your Plan</h3>

          {analysis.career_action_plan.actions.map((action) => (
            <p key={action.title}>
              {action.priority}. {action.title}
            </p>
          ))}
        </section>
      )}
    </main>
  )
}

export default App