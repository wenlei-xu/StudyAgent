import { useChatStore } from '../../store/chatStore'
import { useEffect } from 'react'
import MessageBubble from './MessageBubble'
import ChatInput from './ChatInput'
import QuizCard from '../quiz/QuizCard'
import CheckResult from '../quiz/CheckResult'
import ResourceCard from '../recommendation/ResourceCard'
import ErrorBanner from '../common/ErrorBanner'
import PhaseIndicator from '../common/PhaseIndicator'
import LoadingDots from '../common/LoadingDots'
import KnowledgeGraph from '../knowledge/KnowledgeGraph'
import StagePanel from '../stages/StagePanel'
import HomeworkPanel from '../stages/HomeworkPanel'
import { useAutoScroll } from '../../hooks/useAutoScroll'

interface Props {
  sessionId: string
}

export default function ChatPanel({ sessionId }: Props) {
  const {
    messages,
    streaming,
    quizCard,
    checkResult,
    resourceCards,
    errorMessage,
    currentPhase,
    progress,
    knowledgeMap,
    sendMessage,
    submitAnswer,
    clearError,
    abort,
    // Stage state
    stages,
    homeworkResult,
    stagesLoading,
    fetchStagesAction,
    submitHomeworkAction,
    clearHomeworkResult,
    loadHistory,
  } = useChatStore()

  useEffect(() => {
    loadHistory(sessionId)
  }, [sessionId])

  // Load stages when session changes
  useEffect(() => {
    fetchStagesAction(sessionId)
  }, [sessionId])

  // Find the currently active stage
  const activeStage = stages.find((s) => s.status === 'active')

  // Clear homework result when active stage changes
  useEffect(() => {
    clearHomeworkResult()
  }, [activeStage?.id, sessionId])

  // Show stages loading when streaming and no stages yet (stage_planner is working)
  const showStagesLoading = stagesLoading || (streaming && stages.length === 0 && currentPhase === 'planning')

  const bottomRef = useAutoScroll(messages)

  return (
    <div className="flex flex-col h-full">
      <PhaseIndicator phase={currentPhase} progress={progress} />

      {errorMessage && (
        <ErrorBanner message={errorMessage} onDismiss={clearError} />
      )}

      {/* Stage timeline */}
      <StagePanel
        stages={stages}
        loading={showStagesLoading}
      />

      {/* Active stage homework */}
      {activeStage && (
        <HomeworkPanel
          stage={activeStage}
          result={homeworkResult}
          loading={streaming}
          onSubmit={(answer) => submitHomeworkAction(sessionId, activeStage.id, answer)}
          onClearResult={clearHomeworkResult}
        />
      )}

      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {streaming && messages.length === 0 && <LoadingDots />}

          {quizCard && !checkResult && (
            <QuizCard
              card={quizCard}
              onAnswer={(option) => submitAnswer(sessionId, option)}
              disabled={streaming}
            />
          )}

          {checkResult && (
            <CheckResult result={checkResult} />
          )}

          {resourceCards.length > 0 && (
            <div className="mt-4 space-y-3">
              <h3 className="text-sm font-semibold text-gray-500">学习资源推荐</h3>
              {resourceCards.map((card, i) => (
                <ResourceCard key={i} card={card} />
              ))}
            </div>
          )}

          {Object.keys(knowledgeMap).length > 0 && (
            <div className="mt-4 border border-gray-200 rounded-xl bg-gray-50">
              <KnowledgeGraph knowledgeMap={knowledgeMap} />
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      <ChatInput
        onSend={(text) => sendMessage(sessionId, text)}
        onStop={abort}
        disabled={streaming}
        streaming={streaming}
      />
    </div>
  )
}
