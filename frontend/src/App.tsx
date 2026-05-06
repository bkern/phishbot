import { useState } from 'react'
import { QueryInput } from './components/QueryInput'
import { ResultCard } from './components/ResultCard'

type AppState = 'idle' | 'loading' | 'result' | 'error'

interface Result {
  question: string
  answer: string
  sources: string[]
}

interface ConversationMessage {
  role: 'user' | 'assistant'
  content: string
  sources: string[]
}

export default function App() {
  const [appState, setAppState] = useState<AppState>('idle')
  const [result, setResult] = useState<Result | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState('')
  const [messages, setMessages] = useState<ConversationMessage[]>([])

  function handleNewConversation() {
    setMessages([])
    setResult(null)
    setAppState('idle')
    setError(null)
    setCurrentQuestion('')
  }

  async function handleSubmit(question: string) {
    setAppState('loading')
    setCurrentQuestion(question)
    setError(null)

    const history = messages.map(({ role, content }) => ({ role, content }))

    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, history }),
      })

      if (!response.ok) {
        const body = await response.json()
        throw new Error(body.detail ?? 'Request failed')
      }

      const data = await response.json()
      const newResult = { question, answer: data.answer, sources: data.sources }
      setResult(newResult)
      setMessages(prev => [
        ...prev,
        { role: 'user', content: question, sources: [] },
        { role: 'assistant', content: data.answer, sources: data.sources },
      ])
      setAppState('result')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
      setAppState('error')
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-[#e1e1e1] flex flex-col items-center px-6 py-10">
      <div className="w-full max-w-3xl lg:max-w-5xl xl:max-w-6xl flex flex-col gap-6">

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 bg-[#00c9a0] rounded-[50%_50%_50%_50%/60%_60%_40%_40%] flex items-center justify-center text-xl">
              🐟
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold tracking-tight">
                Phish<span className="text-[#00c9a0]">Bot</span>
              </span>
              <span className="text-xs font-semibold text-[#555] tracking-widest uppercase">AI</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <button
                type="button"
                onClick={handleNewConversation}
                className="text-xs text-[#555] hover:text-[#888] transition-colors px-3 py-1 rounded border border-[#222] hover:border-[#333]"
              >
                New Conversation
              </button>
            )}
            {['setlist.fm', 'phish.net', 'web'].map(src => (
              <span
                key={src}
                className="text-xs text-[#777] bg-[#161616] border border-[#2a2a2a] rounded-full px-3 py-1"
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
          <div className="rounded-xl border border-red-900/40 bg-red-950/20 px-4 py-3 text-sm text-red-400">
            {error}
          </div>
        )}

      </div>
    </div>
  )
}
