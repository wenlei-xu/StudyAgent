"""Test QuizCard structured output generation."""

from app.models.quiz import QuizCard, QuizOption


def test_quiz_card_validation():
    """QuizCard must have valid structure."""
    card = QuizCard(
        id="q_001",
        question="什么是协程？",
        options=[
            QuizOption(key="A", text="一个函数"),
            QuizOption(key="B", text="一个可暂停和恢复的函数"),
        ],
        correct_answer="B",
        explanation="协程是可以暂停和恢复执行的函数。",
        knowledge_point="async/await",
    )
    assert card.id == "q_001"
    assert len(card.options) == 2
    assert card.correct_answer in [o.key for o in card.options]


def test_answer_submission_validation():
    from app.models.quiz import AnswerSubmission

    sub = AnswerSubmission(
        session_id="s1",
        quiz_id="q_001",
        selected_option="B",
    )
    assert sub.selected_option == "B"
