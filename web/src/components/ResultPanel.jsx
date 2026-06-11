import React from 'react'

export default function ResultPanel({ jobId, apiBase }) {
  const base = apiBase || ''

  return (
    <div className="space-y-6">
      <p className="text-green-400 font-medium">
        ✓ Processing complete
      </p>

      <img
        src={`${base}/jobs/${jobId}/result/poster`}
        alt="Aggregate density poster"
        className="w-full rounded border border-gray-700"
      />

      <div className="flex gap-4">
        <a
          href={`${base}/jobs/${jobId}/result/poster`}
          download="poster.png"
          className="flex-1 text-center bg-blue-600
                     hover:bg-blue-500 text-white font-medium
                     py-3 px-4 rounded transition-colors"
        >
          Download Poster PNG
        </a>
        <a
          href={`${base}/jobs/${jobId}/result/zip`}
          download="screenshots.zip"
          className="flex-1 text-center bg-gray-700
                     hover:bg-gray-600 text-white font-medium
                     py-3 px-4 rounded transition-colors"
        >
          Download Screenshots ZIP
        </a>
      </div>
    </div>
  )
}
