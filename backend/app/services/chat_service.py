from app.prompts.coaching import COACHING_SYSTEM, COACHING_USER
from app.services.llm_service import llm_service


class ChatService:
    async def coach(
        self,
        question: dict,
        user_answer: str,
        conversation: list[dict],
        user_message: str,
    ) -> str:
        source_chunk = question.get("source_chunk")
        source_chunk_section = (
            f"\nRelevant source material:\n{source_chunk}"
            if source_chunk
            else ""
        )

        conversation_history = ""
        if conversation:
            conversation_history = "\n".join(
                f"{msg['role'].capitalize()}: {msg['content']}"
                for msg in conversation
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

        return await llm_service.generate(prompt, COACHING_SYSTEM, temperature=0.7)


chat_service = ChatService()
