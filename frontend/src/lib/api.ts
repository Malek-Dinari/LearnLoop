import {
  QuizGenerateRequest,
  QuizGenerateResponse,
  AnswerResponse,
  QuizResults,
  DocumentUploadResponse,
  ChatMessage,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

export async function healthCheck() {
  return request<{ status: string; llm: string; model: string }>("/health");
}

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
}

export async function generateQuiz(req: QuizGenerateRequest): Promise<QuizGenerateResponse> {
  return request<QuizGenerateResponse>("/quiz/generate", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function submitAnswer(
  quizId: string,
  questionId: string,
  answer: string
): Promise<AnswerResponse> {
  return request<AnswerResponse>(`/quiz/${quizId}/answer`, {
    method: "POST",
    body: JSON.stringify({ question_id: questionId, answer }),
  });
}

export async function getQuizResults(quizId: string): Promise<QuizResults> {
  return request<QuizResults>(`/quiz/${quizId}/results`);
}

export async function sendCoachMessage(
  question: Record<string, unknown>,
  userAnswer: string,
  conversation: ChatMessage[],
  message: string
): Promise<{ response: string }> {
  return request<{ response: string }>("/chat/coach", {
    method: "POST",
    body: JSON.stringify({
      question,
      user_answer: userAnswer,
      conversation,
      message,
    }),
  });
}
