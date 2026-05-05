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
    setValue('')
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      handleSubmit()
    }
  }

  return (
    <div className="rounded-xl border border-[#222] bg-[#111] p-5 flex flex-col gap-4 focus-within:border-[#00c9a0] transition-colors">
      <span className="text-xs font-semibold tracking-widest text-[#555] uppercase">Ask</span>
      <textarea
        className="bg-transparent outline-none text-[#e1e1e1] text-lg resize-none placeholder-[#444]"
        rows={3}
        placeholder="Ask anything about Phish..."
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
      />
      <div className="flex items-center justify-between gap-2">
        <div className="flex gap-2 flex-wrap">
          {CHIPS.map(chip => (
            <button
              key={chip}
              type="button"
              onClick={() => setValue(chip)}
              className="text-sm text-[#888] bg-[#1a1a1a] border border-[#2a2a2a] rounded-md px-3 py-1.5 hover:text-[#00c9a0] hover:border-[#00c9a060] transition-colors"
            >
              {chip}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={disabled}
          className="bg-[#00c9a0] text-black font-semibold text-sm rounded-lg px-5 py-2.5 whitespace-nowrap disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Ask →
        </button>
      </div>
    </div>
  )
}
