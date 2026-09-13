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

  const canAnalyze = Boolean(
    resumeFile && jobDescription.trim() && !isAnalyzing,
  )

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="brand-mark" aria-hidden="true">CP</div>
        <div>
          <h1>CareerPilot</h1>
          <p>Turn a resume and job description into a clear, evidence-based action plan.</p>
        </div>
      </header>

      <section className="analysis-form" aria-labelledby="analysis-input-heading">
        <div className="section-heading">
          <div>
            <p className="eyebrow">New analysis</p>
            <h2 id="analysis-input-heading">Compare your experience to the role</h2>
          </div>
          <p className="section-description">Upload a PDF resume and paste the complete job description.</p>
        </div>

        <div className="input-grid">
          <article className="panel input-panel">
            <div className="panel-heading">
              <span className="panel-number" aria-hidden="true">1</span>
              <div>
                <h3>Resume</h3>
                <p>PDF format</p>
              </div>
            </div>

            <label className="file-field" htmlFor="resume">
              <span className="file-icon" aria-hidden="true">↑</span>
              <span className="file-label">
                {resumeFile ? 'Choose a different resume' : 'Choose your resume'}
              </span>
              <span className="file-help">Select a PDF from your device</span>
            </label>
            <input
              className="file-input"
              id="resume"
              type="file"
              accept=".pdf"
              onChange={(event) => {
                const file = event.target.files?.[0] ?? null
                setResumeFile(file)
              }}
            />

            <p className="selected-file" aria-live="polite">
              {resumeFile ? `Selected: ${resumeFile.name}` : 'No file selected'}
            </p>
          </article>

          <article className="panel input-panel">
            <div className="panel-heading">
              <span className="panel-number" aria-hidden="true">2</span>
              <div>
                <h3>Job description</h3>
                <p>Include responsibilities and qualifications</p>
              </div>
            </div>

            <label className="sr-only" htmlFor="job-description">Job Description</label>
            <textarea
              id="job-description"
              value={jobDescription}
              onChange={(event) => setJobDescription(event.target.value)}
              placeholder="Paste the job description here..."
              rows={10}
            />
          </article>
        </div>

        <div className="form-actions">
          <button
            className="analyze-button"
            disabled={!canAnalyze}
            onClick={handleAnalyze}
          >
            {isAnalyzing ? 'Analyzing your fit…' : 'Analyze match'}
          </button>
          <p className="form-note">Analysis may take a moment while evidence and next steps are generated.</p>
        </div>

        {error && (
          <p className="error-message" role="alert">{error}</p>
        )}
      </section>

      {analysis && (
        <section className="results" aria-labelledby="results-heading" aria-live="polite">
          <header className="result-summary">
            <p className="eyebrow">Analysis complete</p>
            <h2 id="results-heading">{analysis.job.job_title}</h2>
            <div className="match-score">
              <strong>{analysis.match_score}%</strong>
              <span>resume match</span>
            </div>
          </header>

          <div className="result-grid">
            <article className="panel result-card strengths-card">
              <div className="result-card-heading">
                <div>
                  <p className="eyebrow positive">Supported qualifications</p>
                  <h3>Strengths</h3>
                </div>
                <span className="count-badge positive">{analysis.strengths.length}</span>
              </div>

              {analysis.strengths.length > 0 ? (
                <ul className="result-list">
                  {analysis.strengths.map((strength) => (
                    <li key={strength.area}>
                      <span className="status-icon matched" aria-hidden="true">✓</span>
                      <div>
                        <h4>{strength.area}</h4>
                        <p>{strength.reason}</p>
                        {strength.evidence && <p className="evidence">{strength.evidence}</p>}
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="empty-state">No matched qualifications were returned.</p>
              )}
            </article>

            <article className="panel result-card gaps-card">
              <div className="result-card-heading">
                <div>
                  <p className="eyebrow caution">Opportunities to improve</p>
                  <h3>Gaps</h3>
                </div>
                <span className="count-badge caution">{analysis.gaps.length}</span>
              </div>

              {analysis.gaps.length > 0 ? (
                <ul className="result-list">
                  {analysis.gaps.map((gap) => (
                    <li key={gap.area}>
                      <span
                        className={`status-icon ${gap.status}`}
                        aria-hidden="true"
                      >
                        {gap.status === 'missing' ? '×' : '△'}
                      </span>
                      <div>
                        <div className="gap-title-row">
                          <h4>{gap.area}</h4>
                          <span className={`status-label ${gap.status}`}>{gap.status}</span>
                        </div>
                        <p>{gap.reason}</p>
                        {gap.evidence && <p className="evidence">{gap.evidence}</p>}
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="empty-state">No qualification gaps were returned.</p>
              )}
            </article>
          </div>

          <article className="panel plan-card">
            <div className="result-card-heading">
              <div>
                <p className="eyebrow plan">Prioritized next steps</p>
                <h3>Career action plan</h3>
              </div>
              <span className="count-badge plan">{analysis.career_action_plan.actions.length}</span>
            </div>

            {analysis.career_action_plan.actions.length > 0 ? (
              <ol className="plan-list">
                {analysis.career_action_plan.actions.map((action) => (
                  <li key={action.title}>
                    <span className="step-number" aria-hidden="true">{action.priority}</span>
                    <div className="plan-content">
                      <h4>{action.title}</h4>
                      <p>{action.description}</p>
                      <div className="plan-meta">
                        {action.addresses_gaps.length > 0 && (
                          <span>Addresses: {action.addresses_gaps.join(', ')}</span>
                        )}
                        {action.depends_on.length > 0 && (
                          <span>After: {action.depends_on.join(', ')}</span>
                        )}
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="empty-state">No career actions are needed for the returned gaps.</p>
            )}
          </article>
        </section>
      )}
    </main>
  )
}

export default App
