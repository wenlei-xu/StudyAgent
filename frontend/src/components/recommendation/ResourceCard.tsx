import type { ResourceCard as ResourceCardType } from '../../api/types'

interface Props {
  card: ResourceCardType
}

export default function ResourceCard({ card }: Props) {
  return (
    <a
      href={card.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block p-4 rounded-xl border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-all no-underline"
    >
      <h5 className="text-sm font-semibold text-blue-700 mb-1">{card.title}</h5>
      <p className="text-xs text-gray-500 mb-1">{card.summary}</p>
      <p className="text-xs text-gray-400">{card.relevance}</p>
    </a>
  )
}
