"use client"

import { useState, useEffect } from "react"

export default function SimpleTestPage() {
  const [result, setResult] = useState<string>("")
  const [error, setError] = useState<string>("")

  useEffect(() => {
    const testAPI = async () => {
      try {
        console.log('Testing API...')
        const response = await fetch('http://localhost:8000/api/cronjobs/')
        console.log('Response status:', response.status)
        
        if (response.ok) {
          const data = await response.json()
          console.log('API data:', data)
          setResult(`Success: ${data.length} jobs found`)
        } else {
          setError(`HTTP ${response.status}: ${response.statusText}`)
        }
      } catch (err) {
        console.error('API error:', err)
        setError(err instanceof Error ? err.message : 'Unknown error')
      }
    }

    testAPI()
  }, [])

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Simple API Test</h1>
      
      {result && (
        <div className="p-4 bg-green-100 border border-green-400 text-green-700 rounded mb-4">
          {result}
        </div>
      )}
      
      {error && (
        <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded">
          Error: {error}
        </div>
      )}
      
      <div className="mt-4">
        <p>Check browser console for detailed logs.</p>
      </div>
    </div>
  )
} 