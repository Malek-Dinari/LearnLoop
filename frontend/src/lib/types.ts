export interface Question {
  id: string;
  type: "mcq" | "true_false" | "short_answer";
  question: string;
  options: string[] | null;
  correct_answer: string;
  explanation: string;
  source_chunk: string | null;
  difficulty: "easy" | "medium" | "hard";
}

export interface QuizGenerateRequest {
  source_type: "topic" | "document";
  topic?: string;
  document_id?: string;
  num_questions: number;
  question_types: string[];
}

export interface QuizGenerateResponse {
  quiz_id: string;
  questions: Question[];
}

export interface AnswerResponse {
  is_correct: boolean;
  score: number;
  feedback: string;
  correct_answer: string;
}

export interface QuestionWithResult extends Question {
  user_answer: string;
  is_correct: boolean;
  score: number;
  feedback: string;
}

export interface QuizResults {
  score: number;
  total: number;
  percentage: number;
  per_type: Record<string, string>;
  coaching_message: string;
  weak_areas: string[];
  questions_with_results: QuestionWithResult[];
}

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  chunk_count: number;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export type QuizState =
  | "IDLE"
  | "GENERATING"
  | "STREAMING"
  | "READY"
  | "IN_PROGRESS"
  | "REVIEWING"
  | "COMPLETE"
  | "COACHING";

// SSE event types from GET /api/quiz/generate/stream
export interface SSEStartEvent {
  type: "start";
  total: number;
  batches: number;
}
export interface SSEQuestionEvent {
  type: "question";
  question: Question;
  index: number;
}
export interface SSEErrorEvent {
  type: "error";
  message: string;
  batch?: number;
  fatal?: boolean;
}
export interface SSECompleteEvent {
  type: "complete";
  quiz_id: string;
  total: number;
}
export type SSEEvent = SSEStartEvent | SSEQuestionEvent | SSEErrorEvent | SSECompleteEvent;
