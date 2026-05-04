import { useState, KeyboardEvent } from 'react'

const CHIPS = ['longest Tweezer?', 'Maze in first set 2024', 'Carini stats']

interface Props {
  onSubmit: (question: string) => void
  disabled: boolean
}

export function QueryInput({ onSubmit, disabled }: Props) {
  const [value, setValue] = useState('')

  function handleSubmit() {
    const trimmed = value.trim()
    if (!trimmed) return
    onSubmit(trimmed)
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      handleSubmit()
    }
  }

  return (
    <div className="rounded-xl border border-[#222] bg-[#111] p-4 flex flex-col gap-3 focus-within:border-[#00c9a0] transition-colors">
      <span className="text-[10px] font-semibold tracking-widest text-[#444] uppercase">Ask</span>
      <textarea
        className="bg-transparent outline-none text-[#e1e1e1] text-base resize-none placeholder-[#333]"
        rows={2}
        placeholder="Ask anything about Phish..."
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
      />
      <div className="flex items-center justify-between gap-2">
        <div className="flex gap-1.5 flex-wrap">
          {CHIPS.map(chip => (
            <button
              key={chip}
              type="button"
              onClick={() => setValue(chip)}
              className="text-[11px] text-[#444] bg-[#161616] border border-[#1e1e1e] rounded-md px-2 py-1 hover:text-[#00c9a0] hover:border-[#00c9a040] transition-colors"
            >
              {chip}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={disabled}
          className="bg-[#00c9a0] text-black font-semibold text-[13px] rounded-lg px-4 py-2 whitespace-nowrap disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Ask →
        </button>
      </div>
    </div>
  )
}
