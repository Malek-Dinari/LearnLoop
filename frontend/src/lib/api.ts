import {
  QuizGenerateRequest,
  QuizGenerateResponse,
  AnswerResponse,
  QuizResults,
  DocumentUploadResponse,
  ChatMessage,
  SSEEvent,
  Flashcard,
} from "./types";
import { authFetch, getToken } from "./auth";

// Use relative /api so requests go through the Next.js dev proxy (same-origin, no CORS).
// In production, set NEXT_PUBLIC_API_URL=https://your-backend.com/api
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers = new Headers(options?.headers);
  if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const res = await authFetch(`${API_BASE}${path}`, { ...options, headers });
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
  const res = await authFetch(`${API_BASE}/documents/upload`, {
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

/**
 * Open an SSE connection to stream quiz questions as they are generated.
 * Returns a cleanup function that closes the EventSource.
 *
 * The Next.js dev proxy (/api/* → localhost:8000/api/*) forwards SSE correctly
 * when backend sets Cache-Control: no-cache and X-Accel-Buffering: no.
 */
export function generateQuizStream(
  params: QuizGenerateRequest,
  onEvent: (event: SSEEvent) => void,
  onError: (error: Error) => void,
): () => void {
  const qs = new URLSearchParams({
    source_type: params.source_type,
    num_questions: String(params.num_questions),
    question_types: params.question_types.join(","),
  });
  if (params.topic) qs.set("topic", params.topic.slice(0, 500));
  if (params.document_id) qs.set("document_id", params.document_id);
  const token = getToken();
  if (token) qs.set("access_token", token);

  const url = `${API_BASE}/quiz/generate/stream?${qs.toString()}`;
  const es = new EventSource(url);

  let connected = false;

  es.onmessage = (e) => {
    connected = true;
    try {
      const data = JSON.parse(e.data) as SSEEvent;
      onEvent(data);
      if (data.type === "complete" || (data.type === "error" && data.fatal)) {
        es.close();
      }
    } catch {
      onError(new Error("Failed to parse SSE event"));
      es.close();
    }
  };

  es.onerror = () => {
    // readyState CLOSED after receiving events = stream finished normally, ignore.
    if (es.readyState === EventSource.CLOSED && connected) return;
    const msg = connected
      ? "Quiz stream dropped mid-generation. Check if Ollama is still running."
      : "Cannot reach backend. Make sure the server is running on port 8000.";
    onError(new Error(msg));
    es.close();
  };

  return () => es.close();
}

export async function generateFlashcards(
  sourceType: "quiz" | "document",
  id: string,
  numCards = 10
): Promise<Flashcard[]> {
  const body =
    sourceType === "quiz"
      ? { source_type: "quiz", quiz_id: id, num_cards: numCards }
      : { source_type: "document", document_id: id, num_cards: numCards };
  const res = await request<{ flashcards: Flashcard[] }>("/flashcards/generate", {
    method: "POST",
    body: JSON.stringify(body),
  });
  return res.flashcards;
}

export async function sendStudyChatMessage(
  message: string,
  conversation: ChatMessage[],
  context = "",
  quizId?: string
): Promise<{ response: string }> {
  return request<{ response: string }>("/chat/study", {
    method: "POST",
    body: JSON.stringify({ message, conversation, context, quiz_id: quizId }),
  });
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
