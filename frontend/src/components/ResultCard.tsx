import ReactMarkdown from 'react-markdown'

interface Props {
  question: string
  answer: string
  sources: string[]
  loading: boolean
}

export function ResultCard({ question, answer, sources, loading }: Props) {
  return (
    <div className="rounded-xl border border-[#1e1e1e] bg-[#111] overflow-hidden">
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#1a1a1a]">
        {loading ? (
          <span className="text-xs font-semibold tracking-widest text-[#555] uppercase">
            Thinking...
          </span>
        ) : (
          <>
            <span className="text-xs font-semibold tracking-widest text-[#555] uppercase">
              Answer
            </span>
            <span className="text-sm text-[#666] italic truncate max-w-sm">
              "{question}"
            </span>
          </>
        )}
      </div>

      <div className="px-5 py-6 min-h-16">
        {loading ? (
          <>
            {/* shimmer keyframe defined in src/index.css */}
            <div
              data-testid="shimmer-bar"
              className="h-0.5 rounded-full"
              style={{
                background: 'linear-gradient(90deg, #111 0%, #00c9a0 50%, #111 100%)',
                backgroundSize: '200% 100%',
                animation: 'shimmer 1.5s infinite',
              }}
            />
          </>
        ) : (
          <div className="prose-phish text-base text-[#d0d0d0] leading-relaxed">
            <ReactMarkdown>{answer}</ReactMarkdown>
          </div>
        )}
      </div>

      {!loading && sources.length > 0 && (
        <div className="flex items-center gap-2 px-5 py-3 border-t border-[#1a1a1a]">
          <span className="text-xs text-[#444]">sources</span>
          {sources.map(src => (
            <span
              key={src}
              className="text-xs text-[#666] bg-[#161616] border border-[#222] rounded px-2 py-0.5"
            >
              {src}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
