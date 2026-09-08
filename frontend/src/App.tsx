import { useState } from 'react'
import './App.css'

function App() {
  const [jobDescription, setJobDescription] = useState('')

  return (
    <main>
      <h1>CareerPilot</h1>
      <p>Analyze your resume against a job description.</p>

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
    </main>
  )
}

export default App