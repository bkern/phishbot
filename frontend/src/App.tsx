import { useState } from 'react'
import { QueryInput } from './components/QueryInput'
import { ResultCard } from './components/ResultCard'

type AppState = 'idle' | 'loading' | 'result' | 'error'

interface Result {
  question: string
  answer: string
  sources: string[]
}

export default function App() {
  const [appState, setAppState] = useState<AppState>('idle')
  const [result, setResult] = useState<Result | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState('')

  async function handleSubmit(question: string) {
    setAppState('loading')
    setCurrentQuestion(question)
    setError(null)

    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })

      if (!response.ok) {
        const body = await response.json()
        throw new Error(body.detail ?? 'Request failed')
      }

      const data = await response.json()
      setResult({ question, answer: data.answer, sources: data.sources })
      setAppState('result')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
      setAppState('error')
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-[#e1e1e1] flex flex-col items-center px-4 py-8">
      <div className="w-full max-w-2xl md:max-w-3xl flex flex-col gap-6">

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 bg-[#00c9a0] rounded-[50%_50%_50%_50%/60%_60%_40%_40%] flex items-center justify-center text-lg">
              🐟
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-[22px] font-bold tracking-tight">
                Phish<span className="text-[#00c9a0]">Bot</span>
              </span>
              <span className="text-[10px] font-semibold text-[#555] tracking-widest uppercase">AI</span>
            </div>
          </div>
          <div className="flex gap-1.5">
            {['setlist.fm', 'phish.net', 'web'].map(src => (
              <span
                key={src}
                className="text-[10px] text-[#444] bg-[#161616] border border-[#222] rounded-full px-2 py-0.5"
              >
                {src}
              </span>
            ))}
          </div>
        </div>

        <QueryInput onSubmit={handleSubmit} disabled={appState === 'loading'} />

        {appState === 'loading' && (
          <ResultCard question={currentQuestion} answer="" sources={[]} loading={true} />
        )}

        {appState === 'result' && result && (
          <ResultCard
            question={result.question}
            answer={result.answer}
            sources={result.sources}
            loading={false}
          />
        )}

        {appState === 'error' && (
          <div className="rounded-xl border border-red-900/40 bg-red-950/20 px-4 py-3 text-[13px] text-red-400">
            {error}
          </div>
        )}

      </div>
    </div>
  )
}
