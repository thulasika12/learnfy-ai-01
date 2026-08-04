"""
AI Recommender — powers the Study Planner (personalized schedules) and can be
extended to recommend notes / resources based on a student's activity.
"""
import json
from typing import List, Optional

from fastapi import HTTPException

from app.services.ai_service import chat_completion

STUDY_PLAN_SYSTEM_PROMPT = (
    "You are an expert academic study planner. Create a personalized day-by-day study plan "
    "strictly as a JSON array and nothing else — no markdown, no commentary, no code fences. "
    'Each item must have exactly this shape: {"day": 1, "tasks": ["task 1", "task 2"]}.'
)


def generate_study_plan(subjects: List[str], hours_per_day: float, days: int, goal: Optional[str] = None) -> List[dict]:
    goal_line = f" The student's overall goal is: {goal}." if goal else ""
    user_prompt = (
        f"Create a {days}-day study plan for these subjects: {', '.join(subjects)}. "
        f"The student can study {hours_per_day} hours per day.{goal_line} "
        "Distribute topics evenly and include short revision/practice tasks."
    )

    raw = chat_completion(STUDY_PLAN_SYSTEM_PROMPT, user_prompt, temperature=0.5)
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        plan = json.loads(cleaned)
        if not isinstance(plan, list) or not plan:
            raise ValueError("Expected a JSON array")
        validated = []
        for item in plan[:days]:
            if not isinstance(item, dict):
                continue
            day = item.get("day")
            tasks = item.get("tasks")
            if isinstance(day, int) and isinstance(tasks, list) and tasks:
                clean_tasks = [str(task).strip() for task in tasks if str(task).strip()]
                if clean_tasks:
                    validated.append({"day": day, "tasks": clean_tasks})
        if not validated:
            raise ValueError("No valid study-plan days were returned")
        return validated
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"AI returned an unexpected format: {exc}") from exc
