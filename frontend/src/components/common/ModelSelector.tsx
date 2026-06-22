import { useState, useRef, useEffect } from 'react'
import { useChatStore } from '../../store/chatStore'

const MODELS = [
  { value: 'deepseek-v4-flash', label: 'DeepSeek V4 Flash' },
  { value: 'deepseek-v4-pro', label: 'DeepSeek V4 Pro' },
  { value: '', label: '默认（自动）' },
]

export default function ModelSelector() {
  const selectedModel = useChatStore((s) => s.selectedModel)
  const setSelectedModel = useChatStore((s) => s.setSelectedModel)
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  const current = MODELS.find((m) => m.value === (selectedModel ?? '')) ?? MODELS[0]

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-700 hover:border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
      >
        <span className="truncate">{current.label}</span>
        <svg
          className={`w-3.5 h-3.5 text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="absolute left-0 right-0 top-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 overflow-hidden">
          {MODELS.map((m) => (
            <button
              key={m.value}
              onClick={() => {
                setSelectedModel(m.value || null)
                setOpen(false)
              }}
              className={`w-full text-left px-3 py-2 text-sm hover:bg-blue-50 transition-colors ${
                (selectedModel ?? '') === m.value
                  ? 'bg-blue-50 text-blue-700 font-medium'
                  : 'text-gray-700'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
