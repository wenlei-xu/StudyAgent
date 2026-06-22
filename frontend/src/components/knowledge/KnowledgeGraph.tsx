import { useMemo } from 'react'
import ReactEChartsCore from 'echarts-for-react/lib/core'
import * as echarts from 'echarts/core'
import { GraphChart } from 'echarts/charts'
import { TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'

echarts.use([GraphChart, TooltipComponent, CanvasRenderer])

interface Props {
  knowledgeMap: Record<string, string>
}

const STATUS_COLORS: Record<string, string> = {
  '已掌握': '#22c55e',
  '学习中': '#f59e0b',
  '未掌握': '#ef4444',
}

const STATUS_ORDER: Record<string, number> = {
  '已掌握': 3,
  '学习中': 2,
  '未掌握': 1,
}

export default function KnowledgeGraph({ knowledgeMap }: Props) {
  if (!knowledgeMap || Object.keys(knowledgeMap).length === 0) {
    return (
      <div className="p-4 text-center text-xs text-gray-400">
        暂无知识点数据，完成答题后出现
      </div>
    )
  }

  const option: EChartsOption = useMemo(() => {
    const entries = Object.entries(knowledgeMap)
    const categories = [
      { name: '已掌握', itemStyle: { color: '#22c55e' } },
      { name: '学习中', itemStyle: { color: '#f59e0b' } },
      { name: '未掌握', itemStyle: { color: '#ef4444' } },
    ]

    return {
      tooltip: {
        formatter: (params: unknown) => {
          const p = params as { name: string; value: number }
          return `${p.name}<br/>掌握度: ${Math.round(p.value * 100)}%`
        },
      },
      series: [
        {
          type: 'graph',
          layout: 'force',
          roam: true,
          draggable: true,
          categories,
          label: { show: true, fontSize: 11, color: '#374151' },
          force: { repulsion: 200, edgeLength: 120 },
          data: entries.map(([name, status]) => ({
            name,
            category: status,
            symbolSize: STATUS_ORDER[status] ? 20 + STATUS_ORDER[status] * 10 : 25,
            value: status === '已掌握' ? 1 : status === '学习中' ? 0.5 : 0.2,
          })),
          links: entries.slice(0, -1).map((_, i) => ({
            source: entries[i][0],
            target: entries[i + 1][0] ?? entries[0][0],
          })),
        },
      ],
    }
  }, [knowledgeMap])

  return (
    <div className="p-3">
      <h4 className="text-xs font-semibold text-gray-500 mb-2">知识图谱</h4>
      <ReactEChartsCore
        echarts={echarts}
        option={option}
        style={{ height: 240 }}
        notMerge
        lazyUpdate
      />
    </div>
  )
}
