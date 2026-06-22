import type { CheckResult as CheckResultType } from '../../api/types'

interface Props {
  result: CheckResultType
}

export default function CheckResult({ result }: Props) {
  return (
    <div
      className={`my-4 p-5 rounded-2xl border shadow-sm ${
        result.correct
          ? 'bg-green-50 border-green-200'
          : 'bg-red-50 border-red-200'
      }`}
    >
      <div className="flex items-center gap-2 mb-3">
        <span
          className={`text-2xl ${result.correct ? '' : ''}`}
        >
          {result.correct ? '✅' : '❌'}
        </span>
        <span
          className={`font-semibold ${
            result.correct ? 'text-green-700' : 'text-red-700'
          }`}
        >
          {result.correct ? '回答正确！' : '回答错误'}
        </span>
      </div>
      {!result.correct && (
        <p className="text-sm text-gray-700 mb-2">
          正确答案：<span className="font-semibold">{result.correct_answer}</span>
        </p>
      )}
      <p className="text-sm text-gray-600 leading-relaxed">{result.explanation}</p>
    </div>
  )
}
