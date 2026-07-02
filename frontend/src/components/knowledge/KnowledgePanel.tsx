import { useState, useEffect, useCallback, useMemo, Component, type ReactNode, useRef } from 'react'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import type { KnowledgeNote, GraphData, SessionResponse } from '../../api/types'
import {
  fetchAllNotes,
  fetchNotes,
  createNote,
  deleteNote,
  fetchGraphData,
  fetchAllGraphData,
} from '../../api/knowledge'
import { listSessions } from '../../api/sessions'

class ChartErrorBoundary extends Component<{children: ReactNode}, {hasError: boolean}> {
  state = {hasError: false}
  static getDerivedStateFromError() { return {hasError: true} }
  render() {
    return this.state.hasError
      ? <div className="text-center text-xs text-gray-400 py-16">图谱渲染失败</div>
      : this.props.children
  }
}

function EChartsGraph({
  option,
  onNodeClick,
  selectedNodeName,
  onCloseCard,
  onViewFull,
  notesMap,
}: {
  option: EChartsOption
  onNodeClick?: (name: string) => void
  selectedNodeName?: string | null
  onCloseCard?: () => void
  onViewFull?: (topic: string) => void
  notesMap?: Map<string, KnowledgeNote>
}) {
  const ref = useRef<HTMLDivElement>(null)
  const instanceRef = useRef<echarts.ECharts | null>(null)
  const [cardStyle, setCardStyle] = useState<{ left: number; top: number } | null>(null)
  const selectedNameRef = useRef<string | null>(null)
  const onNodeClickRef = useRef(onNodeClick)
  const onCloseCardRef = useRef(onCloseCard)
  onNodeClickRef.current = onNodeClick
  onCloseCardRef.current = onCloseCard
  selectedNameRef.current = selectedNodeName ?? null

  const note = selectedNodeName ? notesMap?.get(selectedNodeName) : undefined

  // Calculate card position by iterating data layout
  const syncCardPosition = useCallback(() => {
    const c = instanceRef.current
    const container = ref.current
    const name = selectedNameRef.current
    if (!c || !container || !name) {
      setCardStyle(null)
      return
    }
    try {
      const series = c.getModel().getSeries()[0]
      if (!series) return
      const data = series.getData()
      const count = data.count()
      for (let i = 0; i < count; i++) {
        if (data.getName(i) !== name) continue
        const pos = data.getItemLayout(i)
        if (!pos) return
        const x = Array.isArray(pos) ? pos[0] : (pos as { x: number; y: number }).x
        const y = Array.isArray(pos) ? pos[1] : (pos as { x: number; y: number }).y
        if (x == null || y == null) return

        const cardWidth = 288
        const cardHeight = 180
        const gap = 14
        const pad = 8
        const cw = container.clientWidth
        const ch = container.clientHeight

        let left = x + gap
        if (left + cardWidth > cw - pad) left = x - cardWidth - gap

        let top = y - cardHeight / 2
        if (top < pad) top = pad
        if (top + cardHeight > ch - pad) top = ch - cardHeight - pad

        setCardStyle({ left, top })
        return
      }
      setCardStyle(null)
    } catch {
      setCardStyle(null)
    }
  }, [])

  // Highlight + sync position when selectedNodeName changes
  useEffect(() => {
    const c = instanceRef.current
    if (!c) return
    if (selectedNodeName) {
      c.dispatchAction({ type: 'highlight', seriesIndex: 0, name: selectedNodeName })
      requestAnimationFrame(() => syncCardPosition())
    } else {
      c.dispatchAction({ type: 'downplay', seriesIndex: 0 })
      setCardStyle(null)
    }
  }, [selectedNodeName, syncCardPosition])

  // Init chart once
  useEffect(() => {
    if (!ref.current) return
    const c = echarts.init(ref.current)
    instanceRef.current = c
    c.setOption(option)

    // Handle both node and blank clicks
    c.on('click', (params: { dataType?: string; name?: string; data?: unknown }) => {
      if (params.name) {
        onNodeClickRef.current?.(params.name)
      }
    })
    // Separate handler for blank clicks
    c.getZr().on('click', () => {
      // Blanks reach zr.click but so do nodes — debounce via raf
      requestAnimationFrame(() => {
        if (!selectedNameRef.current) return
      })
    })

    c.on('finished', syncCardPosition)

    const onResize = () => { c.resize(); syncCardPosition() }
    window.addEventListener('resize', onResize)

    return () => {
      window.removeEventListener('resize', onResize)
      c.dispose()
      instanceRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Push option updates without recreating
  useEffect(() => {
    instanceRef.current?.setOption(option, true)
  }, [option])

  return (
    <div ref={ref} style={{ height: '100%', width: '100%', position: 'relative' }}>
      {note && cardStyle && (
        <div
          className="absolute z-30 w-72 bg-white rounded-lg shadow-xl border border-gray-200 flex flex-col"
          style={{ left: cardStyle.left, top: cardStyle.top, pointerEvents: 'auto' }}
        >
          <div className="px-3 py-2 border-b border-gray-100 flex items-center justify-between shrink-0">
            <h4 className="text-xs font-semibold text-gray-800 truncate">{note.topic}</h4>
            <button
              type="button"
              className="text-[10px] text-gray-400 hover:text-gray-600 shrink-0 ml-2"
              onClick={() => onCloseCard?.()}
            >
              ✕
            </button>
          </div>
          <div className="px-3 py-2 overflow-y-auto flex-1">
            <p className="text-[11px] text-gray-600 leading-relaxed line-clamp-4">{note.content}</p>
            {note.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1.5">
                {note.tags.map((tag) => (
                  <span key={tag} className="text-[9px] bg-gray-100 text-gray-400 px-1.5 py-0.5 rounded">{tag}</span>
                ))}
              </div>
            )}
            <button
              type="button"
              className="text-[10px] text-blue-500 hover:text-blue-700 mt-1.5"
              onClick={() => onViewFull?.(selectedNodeName!)}
            >
              查看完整 →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

interface Props {
  sessionId: string
}

export default function KnowledgePanel({ sessionId }: Props) {
  const [open, setOpen] = useState(false)
  const [notes, setNotes] = useState<KnowledgeNote[]>([])
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] })
  const [loading, setLoading] = useState(false)
  const [viewingNote, setViewingNote] = useState<KnowledgeNote | null>(null)
  const [adding, setAdding] = useState(false)
  const [newTopic, setNewTopic] = useState('')
  const [newContent, setNewContent] = useState('')
  const [newTags, setNewTags] = useState('')
  const [collapsedSessions, setCollapsedSessions] = useState<Set<string>>(new Set())
  const [graphModal, setGraphModal] = useState(false)
  const [sessionsList, setSessionsList] = useState<SessionResponse[]>([])
  const [selectedGraphSession, setSelectedGraphSession] = useState('all')
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [notesMap, setNotesMap] = useState<Map<string, KnowledgeNote>>(new Map())
  const [selectedNodeName, setSelectedNodeName] = useState<string | null>(null)

  const reload = useCallback(async () => {
    setLoading(true)
    try {
      const data = await fetchAllNotes()
      setNotes(data)
      // Default all session groups to collapsed
      const keys = [...new Set(data.map((n) => n.session_name || '(未知会话)'))]
      setCollapsedSessions(new Set(keys))
    } finally {
      setLoading(false)
    }
  }, [])

  const loadGraph = useCallback(async (sessionId: string) => {
    const [data, notes] = sessionId === 'all'
      ? await Promise.all([fetchAllGraphData(), fetchAllNotes()])
      : await Promise.all([fetchGraphData(sessionId), fetchNotes(sessionId)])
    setGraphData(data)
    // Build a map of topic name -> note for node click lookup
    setNotesMap(new Map(notes.map((n) => [n.topic, n])))
  }, [])

  // Load sessions list when graph modal opens
  const openGraph = useCallback(async () => {
    setSelectedGraphSession('all')
    setSelectedNodeName(null)
    const [sessions, data, notes] = await Promise.all([
      listSessions(),
      fetchAllGraphData(),
      fetchAllNotes(),
    ])
    setSessionsList(sessions)
    setGraphData(data)
    setNotesMap(new Map(notes.map((n) => [n.topic, n])))
    setGraphModal(true)
  }, [])

  // Reload graph when selected session changes
  useEffect(() => {
    if (graphModal) {
      setSelectedNodeName(null)
      loadGraph(selectedGraphSession)
    }
  }, [selectedGraphSession, loadGraph, graphModal])

  useEffect(() => {
    if (open) reload()
  }, [open, reload])

  const handleAdd = async () => {
    if (!newTopic.trim() || !newContent.trim()) return
    const tags = newTags.split(/[,，\s]+/).filter(Boolean)
    await createNote(sessionId, newTopic.trim(), newContent.trim(), tags)
    setAdding(false)
    setNewTopic('')
    setNewContent('')
    setNewTags('')
    reload()
  }

  const handleDelete = async (noteId: string) => {
    await deleteNote(sessionId, noteId)
    if (viewingNote?.id === noteId) setViewingNote(null)
    reload()
  }

  // Group notes by session_name
  const grouped = notes.reduce<Record<string, KnowledgeNote[]>>((acc, n) => {
    const key = n.session_name || '(未知会话)'
    ;(acc[key] ??= []).push(n)
    return acc
  }, {})
  const groupEntries = Object.entries(grouped)

  const MASTERY_COLORS: Record<string, string> = {
    mastered: '#22c55e',
    learning: '#f59e0b',
    unfamiliar: '#ef4444',
  }

  const graphOption: EChartsOption = useMemo(() => ({
    tooltip: { formatter: (params: unknown) => {
      const p = params as { name: string; data?: { mastery_status?: string | null } }
      let text = p.name
      if (p.data?.mastery_status) {
        const label = { mastered: '已掌握', learning: '学习中', unfamiliar: '未掌握' }[p.data.mastery_status] ?? p.data.mastery_status
        text += `\n掌握程度: ${label}`
      }
      return text
    } },
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      label: { show: true, fontSize: 12, color: '#374151' },
      force: { repulsion: 500, edgeLength: 200 },
      data: graphData.nodes.map((n) => ({
        id: n.id,
        name: n.name,
        symbolSize: n.mastery_status ? 20 + ({ mastered: 30, learning: 20, unfamiliar: 15 }[n.mastery_status] ?? 20) : 25,
        itemStyle: {
          color: n.mastery_status ? MASTERY_COLORS[n.mastery_status] : (n.category === 'auto' ? '#3b82f6' : '#8b5cf6'),
        },
      })),
      links: graphData.edges.map((e) => ({ source: e.source, target: e.target })),
      lineStyle: { color: '#d1d5db', width: 1.5, curveness: 0.2 },
    }],
  }), [graphData])

  const renderNote = (note: KnowledgeNote) => (
    <>
      <h4 className="text-xs font-medium text-gray-800 leading-relaxed cursor-pointer hover:text-blue-600" onClick={() => setViewingNote(note)}>{note.topic}</h4>
      <p className="text-[11px] text-gray-500 mt-1 leading-relaxed line-clamp-2 cursor-pointer" onClick={() => setViewingNote(note)}>{note.content}</p>
      {note.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-1.5">
          {note.tags.map((tag) => (
            <span key={tag} className="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">{tag}</span>
          ))}
        </div>
      )}
      <div className="flex items-center justify-between mt-1">
        <span className="text-[10px] text-gray-300">{note.source_type === 'auto' ? 'AI 自动' : '手动'} &middot; {new Date(note.created_at).toLocaleDateString('zh-CN')}</span>
        <button type="button" className="text-[10px] text-gray-300 hover:text-red-500" onClick={(e) => { e.stopPropagation(); handleDelete(note.id) }}>删除</button>
      </div>
    </>
  )

  return (
    <>
      {/* Collapsed open button */}
      {!open && (
        <button type="button"
          className="fixed right-0 top-1/2 -translate-y-1/2 bg-white border border-gray-200 border-r-0 rounded-l-md px-1.5 py-8 text-xs text-gray-400 hover:text-blue-500 hover:border-blue-200"
          onClick={() => setOpen(true)}
        >
          知识库
        </button>
      )}

      {/* Panel */}
      {open && (
        <div className="w-80 bg-white border-l border-gray-200 flex flex-col h-full relative">
          <button type="button"
            className="absolute -left-3 top-1/2 -translate-y-1/2 w-6 h-6 bg-white border border-gray-200 rounded-full flex items-center justify-center text-gray-400 hover:text-blue-500 text-xs z-10"
            onClick={() => setOpen(false)}
          >
            ▶
          </button>

          <div className="px-3 py-2 border-b border-gray-200">
            <h3 className="text-xs font-semibold text-gray-500">知识笔记</h3>
          </div>

          {/* Notes section - takes remaining space */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="px-3 py-2">
              <button type="button"
                className="w-full text-xs py-1.5 border border-dashed border-gray-300 text-gray-400 rounded-md hover:border-blue-400 hover:text-blue-500"
                onClick={() => setAdding(true)}
              >
                + 添加笔记
              </button>
            </div>

            {adding && (
              <div className="px-3 pb-2 border-b border-gray-100 space-y-1.5">
                <input className="w-full text-xs border border-gray-200 rounded-md px-2 py-1.5 outline-none" placeholder="知识点名称" value={newTopic} onChange={(e) => setNewTopic(e.target.value)} />
                <textarea className="w-full text-xs border border-gray-200 rounded-md px-2 py-1.5 outline-none resize-none" placeholder="笔记内容" rows={3} value={newContent} onChange={(e) => setNewContent(e.target.value)} />
                <input className="w-full text-xs border border-gray-200 rounded-md px-2 py-1.5 outline-none" placeholder="标签 (逗号分隔)" value={newTags} onChange={(e) => setNewTags(e.target.value)} />
                <div className="flex gap-1 justify-end">
                  <button type="button" className="text-xs px-2 py-1 text-gray-500" onClick={() => { setAdding(false); setNewTopic(''); setNewContent(''); setNewTags('') }}>取消</button>
                  <button type="button" className="text-xs px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600" onClick={handleAdd}>保存</button>
                </div>
              </div>
            )}

            <div className="flex-1 overflow-y-auto px-3 pb-2">
              {loading ? (
                <div className="text-center text-xs text-gray-400 py-8">加载中...</div>
              ) : groupEntries.length === 0 ? (
                <div className="text-center text-xs text-gray-400 py-8">
                  暂无笔记<br /><span className="text-gray-300">AI 会在教学后自动生成笔记</span>
                </div>
              ) : (
                <div className="space-y-3 pt-2">
                  {groupEntries.map(([sessionName, sns]) => {
                    const isCollapsed = collapsedSessions.has(sessionName)
                    return (
                      <div key={sessionName} className="border border-gray-100 rounded-lg overflow-hidden">
                        <button type="button"
                          className="w-full flex items-center justify-between px-3 py-2 hover:bg-gray-50 text-left"
                          onClick={() => {
                            const next = new Set(collapsedSessions)
                            if (isCollapsed) next.delete(sessionName)
                            else next.add(sessionName)
                            setCollapsedSessions(next)
                          }}
                        >
                          <span className="text-[11px] font-semibold text-gray-500">{sessionName}</span>
                          <span className="text-[10px] text-gray-300 flex items-center gap-1.5">
                            <span>{sns.length} 条</span>
                            <span className="text-[9px]">{isCollapsed ? '▶' : '▼'}</span>
                          </span>
                        </button>
                        {!isCollapsed && (
                          <div className="px-3 pb-3 space-y-2">
                            {sns.map((note) => (
                              <div key={note.id} className="border border-gray-50 rounded-lg p-2.5 hover:border-gray-200 bg-white">
                                {renderNote(note)}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Graph button - fixed bottom */}
          <div className="border-t border-gray-200 px-3 py-2 shrink-0">
            <button type="button"
              className="w-full text-xs py-1.5 bg-white text-gray-500 rounded-md hover:bg-blue-50 hover:text-blue-600 border border-gray-200"
              onClick={openGraph}
            >
              知识图谱
            </button>
          </div>
        </div>
      )}

      {/* Note detail modal */}
      {viewingNote && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={() => setViewingNote(null)}>
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="px-5 py-4 border-b border-gray-100 flex items-start justify-between gap-4">
              <div>
                <h2 className="text-sm font-semibold text-gray-900">{viewingNote.topic}</h2>
                <p className="text-[11px] text-gray-400 mt-0.5">{viewingNote.session_name || ''} &middot; {new Date(viewingNote.created_at).toLocaleDateString('zh-CN')}</p>
              </div>
              <div className="flex gap-2 shrink-0">
                <button type="button" className="text-[11px] text-red-400 hover:text-red-600" onClick={() => { handleDelete(viewingNote.id); setViewingNote(null) }}>删除</button>
                <button type="button" className="text-[11px] text-gray-400 hover:text-gray-600" onClick={() => setViewingNote(null)}>关闭</button>
              </div>
            </div>
            <div className="px-5 py-4">
              <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{viewingNote.content}</div>
              {viewingNote.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-4">
                  {viewingNote.tags.map((tag) => (
                    <span key={tag} className="text-[11px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded">{tag}</span>
                  ))}
                </div>
              )}
              <span className="text-[11px] text-gray-300 mt-3 block">{viewingNote.source_type === 'auto' ? 'AI 自动生成' : '手动创建'}</span>
            </div>
          </div>
        </div>
      )}

      {/* Graph modal */}
      {graphModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={() => setGraphModal(false)}>
          <div className="bg-white rounded-xl shadow-xl w-[90vw] h-[85vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="px-5 py-3 border-b border-gray-100 grid grid-cols-[1fr_auto_1fr] items-center shrink-0">
              <h2 className="text-sm font-semibold text-gray-900">知识图谱</h2>
              <div className="relative">
                <button
                  type="button"
                  className="text-xs border border-gray-200 rounded-md px-3 py-1.5 text-gray-600 bg-white cursor-pointer hover:border-gray-300 transition-colors flex items-center gap-2 w-48"
                  onClick={() => setDropdownOpen(!dropdownOpen)}
                >
                  <span className="flex-1 text-center truncate">{sessionsList.find(s => s.id === selectedGraphSession)?.learning_goal || '全部会话'}</span>
                  <svg width="10" height="6" fill="#9ca3af" viewBox="0 0 10 6"><path d="M0 0l5 6 5-6z"/></svg>
                </button>
                {dropdownOpen && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setDropdownOpen(false)} />
                    <div className="absolute left-1/2 -translate-x-1/2 top-full mt-1 z-50 bg-white border border-gray-200 rounded-lg shadow-lg py-1 min-w-[160px] w-48">
                      <button
                        type="button"
                        className={`w-full text-center text-xs px-3 py-2 hover:bg-blue-50 transition-colors ${selectedGraphSession === 'all' ? 'text-blue-600 font-medium' : 'text-gray-600'}`}
                        onClick={() => { setSelectedGraphSession('all'); setDropdownOpen(false) }}
                      >
                        全部会话
                      </button>
                      {sessionsList.map((s) => (
                        <button
                          key={s.id}
                          type="button"
                          className={`w-full text-center text-xs px-3 py-2 hover:bg-blue-50 transition-colors truncate ${selectedGraphSession === s.id ? 'text-blue-600 font-medium' : 'text-gray-600'}`}
                          onClick={() => { setSelectedGraphSession(s.id); setDropdownOpen(false) }}
                        >
                          {s.learning_goal}
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </div>
              <button type="button" className="text-xs px-3 py-1 text-gray-400 hover:text-gray-600 justify-self-end" onClick={() => setGraphModal(false)}>关闭</button>
            </div>
            <div className="flex-1 p-4 flex flex-col">
              {graphData.nodes.length === 0 ? (
                <div className="text-center text-xs text-gray-400 py-16">暂无知识点</div>
              ) : (
                <>
                  <div className="flex items-center gap-4 mb-2 text-[11px] text-gray-500 shrink-0">
                    <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-[#22c55e]" /> 已掌握</span>
                    <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-[#f59e0b]" /> 学习中</span>
                    <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-[#ef4444]" /> 未掌握</span>
                    <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-[#3b82f6]" /> 无掌握数据</span>
                  </div>
                  <div className="flex-1 relative">
                    <ChartErrorBoundary>
                      <EChartsGraph
                        option={graphOption}
                        notesMap={notesMap}
                        selectedNodeName={selectedNodeName}
                        onNodeClick={(name) => setSelectedNodeName(selectedNodeName === name ? null : name)}
                        onCloseCard={() => setSelectedNodeName(null)}
                        onViewFull={(topic) => {
                          const note = notesMap.get(topic)
                          if (note) setViewingNote(note)
                        }}
                      />
                    </ChartErrorBoundary>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
