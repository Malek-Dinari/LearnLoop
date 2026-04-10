import logging

from app.prompts.coaching import COACHING_SYSTEM, COACHING_USER
from app.prompts.study_chat import STUDY_CHAT_SYSTEM, STUDY_CHAT_USER
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

MAX_CONVERSATION_MESSAGES = 20


class ChatService:
    async def coach(
        self,
        question: dict,
        user_answer: str,
        conversation: list[dict],
        user_message: str,
    ) -> str:
        # Truncate conversation to prevent context overflow
        recent = conversation[-MAX_CONVERSATION_MESSAGES:]

        source_chunk = question.get("source_chunk")
        source_chunk_section = (
            f"\nRelevant source material:\n{source_chunk}"
            if source_chunk
            else ""
        )

        conversation_history = ""
        if recent:
            conversation_history = "\n".join(
                f"{msg['role'].capitalize()}: {msg['content']}"
                for msg in recent
            )
        else:
            conversation_history = "(This is the start of the conversation)"

        prompt = COACHING_USER.format(
            question=question.get("question", ""),
            correct_answer=question.get("correct_answer", ""),
            user_answer=user_answer,
            source_chunk_section=source_chunk_section,
            conversation_history=conversation_history,
            user_message=user_message,
        )

        try:
            return await llm_service.generate(prompt, COACHING_SYSTEM, temperature=0.7)
        except Exception:
            logger.exception("LLM failure in coach")
            return "I'm having trouble right now. Please try again."

    async def study_chat(
        self,
        context: str,
        conversation: list[dict],
        user_message: str,
        quiz_summary: dict | None = None,
    ) -> str:
        recent = conversation[-MAX_CONVERSATION_MESSAGES:]

        quiz_context_section = ""
        if quiz_summary:
            pct = quiz_summary.get("percentage", 0)
            score = quiz_summary.get("score", 0)
            total = quiz_summary.get("total", 0)
            weak = ", ".join(quiz_summary.get("weak_areas", [])) or "none identified"
            quiz_context_section = (
                f"Quiz context: Student just scored {score}/{total} ({pct:.0f}%). "
                f"Weak areas: {weak}.\n\n"
            )

        if recent:
            conversation_history = "\n".join(
                f"{msg['role'].capitalize()}: {msg['content']}"
                for msg in recent
            )
        else:
            conversation_history = "(Start of conversation)"

        prompt = STUDY_CHAT_USER.format(
            quiz_context_section=quiz_context_section,
            conversation_history=conversation_history,
            user_message=user_message,
        )

        # Prepend context to system if provided
        system = STUDY_CHAT_SYSTEM
        if context.strip():
            system = f"{STUDY_CHAT_SYSTEM}\n\nStudy topic/context: {context[:1000]}"

        try:
            return await llm_service.generate(prompt, system, temperature=0.7)
        except Exception:
            logger.exception("LLM failure in study_chat")
            return "I'm having trouble right now. Please try again."


chat_service = ChatService()
