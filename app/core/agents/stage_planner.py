"""Stage Planner Agent — generates a structured learning plan with stages and homework.

Called when a new session is created. Uses the LLM to break down a learning goal
into sequential stages, each with a description and a homework assignment.
"""

import json

from app.config import settings
from app.core.agents.base import BaseAgent

STAGE_PLANNER_SYSTEM_PROMPT = """你是一个专业的课程设计师。用户告诉你一个学习目标，你需要把它拆分成 3~5 个循序渐进的学习阶段。

## 要求
1. 每个阶段必须有明确的学习主题（title）和详细描述（description）
2. 每个阶段必须有一份**作业**（homework），这份作业要能大致涵盖本阶段需要学习的核心知识
3. 作业必须是具体的、可检验的，不能是模糊的"复习本阶段内容"
4. 阶段的难度要循序渐进
5. 阶段数量根据目标复杂度灵活决定（简单目标 3 个阶段，复杂目标最多 5 个阶段）

## 输出格式
你必须严格按照以下 JSON 格式输出，不要包含任何其他文字：

```json
{
  "stages": [
    {
      "stage_number": 1,
      "title": "阶段标题",
      "description": "本阶段要学习的内容概述",
      "homework": "具体的作业要求，用户完成后由 AI 检查"
    }
  ]
}
```

请确保 JSON 格式正确，每个字段都不为空。"""


class StagePlannerAgent(BaseAgent):
    """Generates learning stages from a user's learning goal."""

    def __init__(self):
        super().__init__(model_name=settings.supervisor_model)

    async def generate_stages(self, learning_goal: str) -> list[dict]:
        """Generate a list of learning stages for the given goal.

        Returns a list of dicts: [{stage_number, title, description, homework}, ...]
        """
        system = STAGE_PLANNER_SYSTEM_PROMPT
        user = f"学习目标：{learning_goal}\n\n请为这个目标设计学习阶段和作业。"

        try:
            # Use structured output — first try JSON mode via generate()
            raw = await self.generate(system, user, model_override=settings.supervisor_model)
            # Extract JSON from the response (may be wrapped in ```json blocks)
            stages = self._parse_stages(raw)
            if stages:
                return stages
        except Exception:
            pass

        # Fallback: manual stages
        return self._fallback_stages(learning_goal)

    def _parse_stages(self, raw: str) -> list[dict] | None:
        """Extract stages JSON from LLM output."""
        # Try to find JSON block
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
            stages = data.get("stages", [])
            if stages and all(
                s.get("title") and s.get("homework") for s in stages
            ):
                # Mark first stage as active, rest as locked
                for i, s in enumerate(stages):
                    s["status"] = "active" if i == 0 else "locked"
                return stages
        except (json.JSONDecodeError, KeyError):
            pass
        return None

    def _fallback_stages(self, learning_goal: str) -> list[dict]:
        """Generate a simple fallback plan when LLM parsing fails."""
        return [
            {
                "stage_number": 1,
                "title": "基础入门",
                "description": f"了解「{learning_goal}」的核心概念和基础知识",
                "homework": f"请用自己的话总结「{learning_goal}」的 3 个核心概念，并给出每个概念的实际应用场景。",
                "status": "active",
            },
            {
                "stage_number": 2,
                "title": "进阶学习",
                "description": f"深入理解「{learning_goal}」的高级特性和最佳实践",
                "homework": f"请完成一个综合练习：结合实际场景，设计一个使用「{learning_goal}」的解决方案，并说明你的设计思路。",
                "status": "locked",
            },
            {
                "stage_number": 3,
                "title": "实战应用",
                "description": f"将「{learning_goal}」应用到实际项目中，巩固学习成果",
                "homework": f"请总结你在学习「{learning_goal}」过程中的收获，并指出你仍存在的疑问。",
                "status": "locked",
            },
        ]
