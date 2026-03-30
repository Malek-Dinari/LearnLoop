import logging

from fastapi import APIRouter, HTTPException

from app.models import (
    QuizGenerateRequest,
    QuizGenerateResponse,
    Question,
    AnswerRequest,
    AnswerResponse,
    QuizResultsResponse,
)
from app.services.quiz_service import quiz_service
from app.services.document_service import document_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/quiz", tags=["quiz"])


@router.post("/generate", response_model=QuizGenerateResponse)
async def generate_quiz(request: QuizGenerateRequest):
    if request.source_type == "topic":
        if not request.topic:
            raise HTTPException(400, "Topic is required for topic-based quizzes")
        content = request.topic
    else:
        if not request.document_id:
            raise HTTPException(400, "Document ID is required for document-based quizzes")
        doc = document_service.get_document(request.document_id)
        if not doc:
            raise HTTPException(404, "Document not found")
        content = "\n\n".join(doc["chunks"])

    try:
        questions = await quiz_service.generate_questions(
            content=content,
            source_type=request.source_type,
            num_questions=request.num_questions,
            question_types=request.question_types,
        )
    except Exception as e:
        logger.exception("Quiz generation failed")
        raise HTTPException(502, f"LLM generation failed: {e}")

    quiz_id = quiz_service.create_quiz(questions)

    return QuizGenerateResponse(
        quiz_id=quiz_id,
        questions=[Question(**q) for q in questions],
    )


@router.post("/{quiz_id}/answer", response_model=AnswerResponse)
async def submit_answer(quiz_id: str, request: AnswerRequest):
    quiz = quiz_service.get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    question = quiz["questions"].get(request.question_id)
    if not question:
        raise HTTPException(404, "Question not found")

    result = await quiz_service.grade_answer(question, request.answer)

    # Store the answer
    quiz["answers"][request.question_id] = {
        "user_answer": request.answer,
        **result,
    }

    return AnswerResponse(**result)


@router.get("/{quiz_id}/results", response_model=QuizResultsResponse)
async def get_results(quiz_id: str):
    quiz = quiz_service.get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    questions_list = list(quiz["questions"].values())
    answers_list = [
        quiz["answers"].get(q["id"], {"user_answer": "", "is_correct": False, "score": 0, "feedback": ""})
        for q in questions_list
    ]

    summary = await quiz_service.generate_quiz_summary(questions_list, answers_list)
    return QuizResultsResponse(**summary)
