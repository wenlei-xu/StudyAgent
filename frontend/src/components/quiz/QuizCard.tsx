import type { QuizCard as QuizCardType } from '../../api/types'

interface Props {
  card: QuizCardType
  onAnswer: (option: string) => void
  disabled?: boolean
}

export default function QuizCard({ card, onAnswer, disabled }: Props) {
  return (
    <div className="my-4 p-5 bg-gradient-to-br from-indigo-50 to-blue-50 rounded-2xl border border-indigo-100 shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xs font-medium text-indigo-500 bg-indigo-100 px-2 py-0.5 rounded-full">
          题目
        </span>
        <span className="text-xs text-gray-400">{card.knowledge_point}</span>
      </div>
      <h4 className="text-base font-semibold text-gray-900 mb-4">{card.question}</h4>
      <div className="space-y-2">
        {card.options.map((opt) => (
          <button
            key={opt.key}
            onClick={() => onAnswer(opt.key)}
            disabled={disabled}
            className="w-full text-left px-4 py-3 rounded-xl border border-gray-200 bg-white hover:border-indigo-400 hover:bg-indigo-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm"
          >
            <span className="font-semibold text-indigo-600 mr-2">{opt.key}.</span>
            {opt.text}
          </button>
        ))}
      </div>
    </div>
  )
}
