interface Props {
  message: string
  onDismiss: () => void
}

export default function ErrorBanner({ message, onDismiss }: Props) {
  return (
    <div className="bg-red-50 border-b border-red-200 px-4 py-2 flex items-center justify-between">
      <span className="text-sm text-red-700">{message}</span>
      <button
        onClick={onDismiss}
        className="text-red-400 hover:text-red-600 text-sm font-medium"
      >
        关闭
      </button>
    </div>
  )
}
