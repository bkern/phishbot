interface Props {
  question: string
  answer: string
  sources: string[]
  loading: boolean
}

export function ResultCard({ question, answer, sources, loading }: Props) {
  return (
    <div className="rounded-xl border border-[#1e1e1e] bg-[#111] overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#1a1a1a]">
        {loading ? (
          <span className="text-[10px] font-semibold tracking-widest text-[#444] uppercase">
            Thinking...
          </span>
        ) : (
          <>
            <span className="text-[10px] font-semibold tracking-widest text-[#444] uppercase">
              ANSWER
            </span>
            <span className="text-[12px] text-[#555] italic truncate max-w-xs">
              "{question}"
            </span>
          </>
        )}
      </div>

      <div className="px-4 py-5 min-h-16">
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
          <p className="text-[15px] text-[#ccc] leading-relaxed">{answer}</p>
        )}
      </div>

      {!loading && sources.length > 0 && (
        <div className="flex items-center gap-2 px-4 py-2.5 border-t border-[#1a1a1a]">
          <span className="text-[10px] text-[#333]">sources</span>
          {sources.map(src => (
            <span
              key={src}
              className="text-[10px] text-[#444] bg-[#161616] border border-[#1e1e1e] rounded px-1.5 py-0.5"
            >
              {src}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
