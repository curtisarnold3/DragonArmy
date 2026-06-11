import React from 'react'

export default function ProgressBar({ stage, percent, stages }) {
  return (
    <div className="space-y-4">
      <div className="flex justify-between text-sm
                      text-gray-400 mb-1">
        <span className="capitalize">{stage || 'Starting…'}</span>
        <span>{percent}%</span>
      </div>
      <div className="w-full bg-gray-800 rounded-full h-3">
        <div
          className="bg-blue-500 h-3 rounded-full transition-all
                     duration-500"
          style={{ width: `${percent}%` }}
        />
      </div>
      <div className="flex justify-between text-xs
                      text-gray-600 mt-2">
        {stages.map((s) => (
          <span
            key={s}
            className={s === stage ? 'text-blue-400 font-medium'
                                   : ''}
          >
            {s}
          </span>
        ))}
      </div>
    </div>
  )
}
