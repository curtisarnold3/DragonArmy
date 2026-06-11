import React, { useState } from 'react'
import Dropzone from './components/Dropzone'
import ProgressBar from './components/ProgressBar'
import ResultPanel from './components/ResultPanel'

const STAGES = [
  'probe', 'calibrate', 'base_map', 'segment',
  'screenshots', 'detect', 'seam_roll', 'render',
  'compose', 'save', 'zip', 'done'
]

export default function App() {
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState('idle')
  // idle | uploading | running | done | error
  const [stage, setStage] = useState('')
  const [percent, setPercent] = useState(0)
  const [error, setError] = useState(null)

  async function handleUpload(file) {
    setStatus('uploading')
    setError(null)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch('/jobs', {
        method: 'POST',
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
    const es = new EventSource(`/jobs/${id}/events`)
    es.onmessage = (e) => {
      const data = JSON.parse(e.data)
      setStage(data.stage)
      setPercent(data.percent)
      if (data.status === 'done') {
        setStatus('done')
        es.close()
      } else if (data.status === 'error') {
        setStatus('error')
        setError('Pipeline failed')
        es.close()
      }
    }
    es.onerror = () => {
      es.close()
      // Fall back to polling
      const interval = setInterval(async () => {
        const res = await fetch(`/jobs/${id}`)
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
  }

  return (
    <div className="max-w-3xl mx-auto py-12 px-4">
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
    </div>
  )
}
