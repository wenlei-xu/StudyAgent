import { useState, useRef } from 'react'

interface Props {
  onSend: (text: string) => void
  onStop: () => void
  disabled?: boolean
  streaming?: boolean
}

export default function ChatInput({ onSend, onStop, disabled, streaming }: Props) {
  const [text, setText] = useState('')
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
    inputRef.current?.focus()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (streaming) {
        onStop()
      } else {
        handleSend()
      }
    }
  }

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <div className="flex gap-2 items-end max-w-3xl mx-auto">
        <textarea
          ref={inputRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={streaming ? 'AI 正在生成…' : '输入你的问题… (Enter 发送, Shift+Enter 换行)'}
          disabled={disabled && !streaming}
          rows={1}
          className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50"
        />
        {streaming ? (
          <button
            onClick={onStop}
            className="px-5 py-3 bg-red-500 text-white text-sm font-medium rounded-xl hover:bg-red-600 transition-colors shrink-0"
          >
            ⏹ 停止
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={disabled || !text.trim()}
            className="px-5 py-3 bg-blue-600 text-white text-sm font-medium rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shrink-0"
          >
            发送
          </button>
        )}
      </div>
    </div>
  )
}
