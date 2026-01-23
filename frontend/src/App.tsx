import { useEffect, useState } from 'react'

function App() {
  const [apiStatus, setApiStatus] = useState<string>('Checking...')

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then((res) => res.json())
      .then((data) => setApiStatus(data.status))
      .catch(() => setApiStatus('Error connecting to API'))
  }, [])

  return (
    <div className='min-h-screen bg-gray-50 flex items-center justify-center p-8'>
      <div className='text-center'>
        <h1 className='text-5xl font-bold text-gray-900 mb-4'>Wavelength</h1>
        <p className='text-xl text-gray-600 mb-8'>Find what resonates</p>
        <div className='bg-white px-6 py-3 rounded-lg shadow-sm'>
          <p className='text-sm text-gray-500'>
            API Status:{' '}
            <span className='font-semibold text-gray-900'>{apiStatus}</span>
          </p>
        </div>
      </div>
    </div>
  )
}

export default App
