import { useChatStore } from '../../store/chatStore'
import MessageBubble from './MessageBubble'
import ChatInput from './ChatInput'
import QuizCard from '../quiz/QuizCard'
import CheckResult from '../quiz/CheckResult'
import ResourceCard from '../recommendation/ResourceCard'
import ErrorBanner from '../common/ErrorBanner'
import PhaseIndicator from '../common/PhaseIndicator'
import LoadingDots from '../common/LoadingDots'
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
    sendMessage,
    submitAnswer,
    clearError,
  } = useChatStore()

  const bottomRef = useAutoScroll(messages)

  return (
    <div className="flex flex-col h-full">
      <PhaseIndicator phase={currentPhase} progress={progress} />

      {errorMessage && (
        <ErrorBanner message={errorMessage} onDismiss={clearError} />
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

          <div ref={bottomRef} />
        </div>
      </div>

      <ChatInput
        onSend={(text) => sendMessage(sessionId, text)}
        disabled={streaming}
      />
    </div>
  )
}
