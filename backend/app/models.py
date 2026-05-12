from pydantic import BaseModel, EmailStr, Field
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
    num_questions: int = Field(default=10, ge=1, le=50)
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
    expert_verified: bool = False


class QuizGenerateResponse(BaseModel):
    quiz_id: str
    questions: list[Question]


class AnswerRequest(BaseModel):
    question_id: str
    answer: str = Field(max_length=5000)


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
    conversation: list[dict] = Field(default_factory=list, max_length=100)
    message: str = Field(max_length=2000)


class CoachResponse(BaseModel):
    response: str


# ── Flashcard schemas ───────────────────────────────────────────────────────

class FlashcardGenerateRequest(BaseModel):
    source_type: str = Field(..., pattern="^(quiz|document)$")
    quiz_id: Optional[str] = None
    document_id: Optional[str] = None
    num_cards: int = Field(default=10, ge=1, le=30)


class Flashcard(BaseModel):
    id: str
    front: str
    back: str
    category: str
    question_id: Optional[str] = None


class FlashcardGenerateResponse(BaseModel):
    flashcards: list[Flashcard]


# ── Study chat schemas ──────────────────────────────────────────────────────

class StudyChatRequest(BaseModel):
    context: str = Field(default="", max_length=2000)
    conversation: list[dict] = Field(default_factory=list, max_length=100)
    message: str = Field(max_length=2000)
    quiz_id: Optional[str] = None


class StudyChatResponse(BaseModel):
    response: str


# ── Auth schemas ────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: str
    email: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Expert-in-the-Loop schemas ──────────────────────────────────────────────

class CorrectionSubmitRequest(BaseModel):
    original_question: Optional[dict] = None
    corrected_question: dict
    topic_tags: list[str] = Field(default_factory=list, max_length=10)


class CorrectionResponse(BaseModel):
    id: str
    original_question: Optional[dict]
    corrected_question: dict
    topic_tags: list[str]
    expert_id: str
    approved: bool
    created_at: str
