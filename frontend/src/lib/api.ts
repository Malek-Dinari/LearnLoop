import {
  QuizGenerateRequest,
  QuizGenerateResponse,
  AnswerResponse,
  QuizResults,
  DocumentUploadResponse,
  ChatMessage,
  SSEEvent,
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

  const url = `${API_BASE}/quiz/generate/stream?${qs.toString()}`;
  const es = new EventSource(url);

  es.onmessage = (e) => {
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
    onError(new Error("SSE connection failed or closed unexpectedly"));
    es.close();
  };

  return () => es.close();
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
