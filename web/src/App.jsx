import React, { useState } from 'react'
import Dropzone from './components/Dropzone'
import ProgressBar from './components/ProgressBar'
import ResultPanel from './components/ResultPanel'

const STAGES = [
  'probe', 'calibrate', 'base_map', 'segment',
  'screenshots', 'detect', 'seam_roll', 'render',
  'compose', 'save', 'zip', 'done'
]

const API_BASE = import.meta.env.VITE_API_URL || ''

export default function App() {
  const [authed, setAuthed] = useState(false)
  const [creds, setCreds] = useState({u:'', p:''})
  const [authError, setAuthError] = useState(false)

  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState('idle')
  // idle | uploading | running | done | error
  const [stage, setStage] = useState('')
  const [percent, setPercent] = useState(0)
  const [error, setError] = useState(null)

  const authHeader = {
    Authorization: 'Basic ' + btoa(creds.u + ':' + creds.p)
  }

  async function handleLogin() {
    const res = await fetch(`${API_BASE}/jobs/healthcheck`, {
      headers: {
        Authorization: 'Basic ' + btoa(creds.u + ':' + creds.p)
      }
    })
    if (res.status === 401) {
      setAuthError(true)
    } else {
      setAuthed(true)
      setAuthError(false)
    }
  }

  async function handleUpload(file) {
    setStatus('uploading')
    setError(null)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_BASE}/jobs`, {
        method: 'POST',
        headers: authHeader,
        body: formData,
      })
      if (!res.ok) throw new Error(await res.text())
      const { job_id } = await res.json()
      setJobId(job_id)
      setStatus('running')
      pollJob(job_id)
    } catch (e) {
      setStatus('error')
      setError(e.message)
    }
  }

  function pollJob(id) {
    const interval = setInterval(async () => {
      const res = await fetch(`${API_BASE}/jobs/${id}`,
        { headers: authHeader })
      const data = await res.json()
      setStage(data.stage)
      setPercent(data.percent)
      if (data.status === 'done') {
        setStatus('done')
        clearInterval(interval)
      } else if (data.status === 'error') {
        setStatus('error')
        setError(data.error)
        clearInterval(interval)
      }
    }, 2000)
  }

  return (
    <div className="max-w-3xl mx-auto py-12 px-4">
      {!authed ? (
        <div className="max-w-sm mx-auto py-24 px-4">
          <h1 className="text-2xl font-bold text-white mb-8">
            GNSS Spoofing Aggregator
          </h1>
          <div className="space-y-4">
            <input
              type="text"
              placeholder="Username"
              value={creds.u}
              onChange={e => setCreds({...creds, u: e.target.value})}
              className="w-full bg-gray-800 text-white px-4 py-2
                         rounded border border-gray-600"
            />
            <input
              type="password"
              placeholder="Password"
              value={creds.p}
              onChange={e => setCreds({...creds, p: e.target.value})}
              onKeyDown={e => e.key === 'Enter' && handleLogin()}
              className="w-full bg-gray-800 text-white px-4 py-2
                         rounded border border-gray-600"
            />
            {authError && (
              <p className="text-red-400 text-sm">Invalid credentials</p>
            )}
            <button
              onClick={handleLogin}
              className="w-full bg-blue-600 hover:bg-blue-500
                         text-white font-medium py-2 rounded"
            >
              Sign in
            </button>
          </div>
        </div>
      ) : (
        <>
          <h1 className="text-2xl font-bold text-white mb-2">
            GNSS Spoofing Aggregator
          </h1>
          <p className="text-gray-400 mb-8 text-sm">
            Upload a Slingshot GNSS spoofing MP4 to generate
            an aggregate density poster and screenshots.
          </p>

          {status === 'idle' && (
            <Dropzone onUpload={handleUpload} />
          )}

          {(status === 'uploading' || status === 'running') && (
            <ProgressBar
              stage={stage}
              percent={percent}
              stages={STAGES}
            />
          )}

          {status === 'done' && (
            <ResultPanel jobId={jobId} />
          )}

          {status === 'error' && (
            <div className="bg-red-900 border border-red-500
                            rounded p-4 text-red-200">
              <p className="font-semibold">Error</p>
              <p className="text-sm mt-1">{error}</p>
              <button
                onClick={() => {
                  setStatus('idle')
                  setError(null)
                  setJobId(null)
                  setPercent(0)
                }}
                className="mt-3 text-sm underline text-red-300
                           hover:text-white"
              >
                Try again
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
