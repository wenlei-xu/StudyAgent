"""Homework Checker Agent — evaluates user homework submissions for a learning stage.

Decides whether the user's submission demonstrates sufficient understanding
to pass the current stage and unlock the next one.
"""

import json

from app.config import settings
from app.core.agents.base import BaseAgent

HOMEWORK_CHECKER_SYSTEM_PROMPT = """你是一个严格但公正的作业批改老师。你需要评估学生的作业是否达到了当前学习阶段的要求。

## 评估标准
1. 作业是否切实回答了要求的问题
2. 回答是否展现了本阶段应有的理解深度
3. 回答是否具体、有实质内容（而非泛泛而谈）
4. 如果作业要求写代码或设计，是否有具体可行的方案

## 输出格式
你必须严格按照以下 JSON 格式输出：

```json
{
  "passed": true,
  "feedback": "详细的批改反馈，包括：哪些地方做得好，哪些地方可以改进，以及对学生的鼓励",
  "stage_number": 1
}
```

- `passed` 为 true 表示通过，可以解锁下一阶段
- `passed` 为 false 表示未通过，需要根据反馈改进后重新提交
- `feedback` 要具体、有建设性，不少于 50 字
- 不要太严格也不要太宽松：如果学生确实展现了理解，就通过；如果明显敷衍或理解错误，就不通过
"""


class HomeworkCheckerAgent(BaseAgent):
    """Evaluates homework submissions and decides pass/fail."""

    def __init__(self):
        super().__init__(model_name=settings.checker_model)

    async def check_homework(
        self,
        learning_goal: str,
        stage_title: str,
        stage_description: str,
        homework: str,
        user_answer: str,
    ) -> dict:
        """Evaluate homework and return {passed, feedback, stage_number}."""
        system = HOMEWORK_CHECKER_SYSTEM_PROMPT
        user = f"""学习目标：{learning_goal}

当前阶段：{stage_title}
阶段内容：{stage_description}
阶段作业：{homework}

学生提交的作业答案：
---
{user_answer}
---

请评估这份作业，按照 JSON 格式输出结果。"""

        try:
            raw = await self.generate(system, user, model_override=settings.checker_model)
            result = self._parse_result(raw)
            if result:
                return result
        except Exception:
            pass

        # Fallback
        return {
            "passed": True,
            "feedback": "作业已收到。由于系统原因，本次自动通过。请继续下一阶段的学习。",
            "stage_number": 1,
        }

    def _parse_result(self, raw: str) -> dict | None:
        """Extract check result JSON from LLM output."""
        json_str = raw
        if "```json" in raw:
            start = raw.index("```json") + 7
            end = raw.index("```", start)
            json_str = raw[start:end].strip()
        elif "```" in raw:
            start = raw.index("```") + 3
            end = raw.index("```", start)
            json_str = raw[start:end].strip()

        try:
            data = json.loads(json_str)
            if "passed" in data and "feedback" in data:
                return {
                    "passed": bool(data["passed"]),
                    "feedback": str(data["feedback"]),
                    "stage_number": int(data.get("stage_number", 1)),
                }
        except (json.JSONDecodeError, KeyError, ValueError):
            pass
        return None
