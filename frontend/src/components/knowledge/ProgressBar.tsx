interface Props {
  progress: number
  size?: 'sm' | 'lg'
  showLabel?: boolean
}

export default function ProgressBar({ progress, size = 'sm', showLabel = true }: Props) {
  const pct = Math.round(progress * 100)
  const height = size === 'lg' ? 'h-3' : 'h-1.5'

  return (
    <div className="flex items-center gap-2">
      <div className={`flex-1 bg-gray-100 rounded-full overflow-hidden ${height}`}>
        <div
          className="h-full bg-blue-500 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-xs text-gray-400 tabular-nums w-9 text-right">
          {pct}%
        </span>
      )}
    </div>
  )
}
