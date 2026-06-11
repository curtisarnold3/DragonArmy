import React, { useCallback } from 'react'

export default function Dropzone({ onUpload }) {
  const handleDrop = useCallback((e) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file && file.name.endsWith('.mp4')) {
      onUpload(file)
    }
  }, [onUpload])

  const handleChange = (e) => {
    const file = e.target.files[0]
    if (file) onUpload(file)
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
      className="border-2 border-dashed border-gray-600
                 rounded-lg p-16 text-center cursor-pointer
                 hover:border-blue-400 transition-colors"
    >
      <p className="text-gray-400 mb-4">
        Drop an MP4 here or click to select
      </p>
      <label className="cursor-pointer bg-blue-600
                        hover:bg-blue-500 text-white text-sm
                        font-medium py-2 px-4 rounded">
        Choose file
        <input
          type="file"
          accept=".mp4"
          className="hidden"
          onChange={handleChange}
        />
      </label>
      <p className="text-gray-600 text-xs mt-4">
        MP4 only · Slingshot GNSS SPOOFING (Standard) layout
      </p>
    </div>
  )
}
