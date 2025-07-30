"use client"

import { useState } from "react"
import useSWR from "swr"

export default function SWRTestPage() {
  const [testKey, setTestKey] = useState("test")

  const { data, error, isLoading } = useSWR(
    testKey,
    async () => {
      console.log('SWR test fetcher called')
      const response = await fetch('http://localhost:8000/api/cronjobs/')
      console.log('SWR test response:', response.status)
      if (response.ok) {
        const data = await response.json()
        console.log('SWR test data:', data)
        return data
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    }
  )

  console.log('SWR test state:', { data, error, isLoading })

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">SWR Test Page</h1>
      
      <button 
        onClick={() => setTestKey(`test-${Date.now()}`)}
        className="px-4 py-2 bg-blue-500 text-white rounded mb-4"
      >
        Refresh Data
      </button>
      
      <div className="space-y-4">
        <div>
          <strong>Loading:</strong> {isLoading ? 'Yes' : 'No'}
        </div>
        
        <div>
          <strong>Error:</strong> {error ? error.message : 'None'}
        </div>
        
        <div>
          <strong>Data:</strong> {data ? `${data.length} jobs` : 'None'}
        </div>
      </div>
      
      <div className="mt-4">
        <p>Check browser console for detailed logs.</p>
      </div>
    </div>
  )
} 