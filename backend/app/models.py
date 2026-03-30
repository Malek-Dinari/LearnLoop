from pydantic import BaseModel, Field
from typing import Optional


class HealthResponse(BaseModel):
    status: str
    llm: str
    model: str


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    chunk_count: int


class QuizGenerateRequest(BaseModel):
    source_type: str = Field(..., pattern="^(topic|document)$")
    topic: Optional[str] = None
    document_id: Optional[str] = None
    num_questions: int = Field(default=10, ge=1, le=20)
    question_types: list[str] = Field(default=["mcq", "true_false", "short_answer"])


class Question(BaseModel):
    id: str
    type: str
    question: str
    options: Optional[list[str]] = None
    correct_answer: str
    explanation: str
    source_chunk: Optional[str] = None
    difficulty: str


class QuizGenerateResponse(BaseModel):
    quiz_id: str
    questions: list[Question]


class AnswerRequest(BaseModel):
    question_id: str
    answer: str


class AnswerResponse(BaseModel):
    is_correct: bool
    score: float
    feedback: str
    correct_answer: str


class QuizResultsResponse(BaseModel):
    score: int
    total: int
    percentage: float
    per_type: dict
    coaching_message: str
    weak_areas: list[str]
    questions_with_results: list[dict]


class CoachRequest(BaseModel):
    question: dict
    user_answer: str
    conversation: list[dict] = Field(default_factory=list)
    message: str


class CoachResponse(BaseModel):
    response: str
