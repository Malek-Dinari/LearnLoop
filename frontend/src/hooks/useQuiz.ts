"use client";

import { useState, useCallback, useRef } from "react";
import {
  Question,
  QuizState,
  AnswerResponse,
  QuizResults,
  ChatMessage,
  SSEEvent,
} from "@/lib/types";
import {
  generateQuizStream,
  submitAnswer,
  getQuizResults,
  uploadDocument,
  sendCoachMessage,
} from "@/lib/api";

interface AnswerRecord {
  questionId: string;
  answer: string;
  result: AnswerResponse;
}

export interface StreamProgress {
  received: number;
  total: number;
}

export function useQuiz() {
  const [state, setState] = useState<QuizState>("IDLE");
  const [quizId, setQuizId] = useState<string>("");
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<AnswerRecord[]>([]);
  const [currentFeedback, setCurrentFeedback] = useState<AnswerResponse | null>(null);
  const [results, setResults] = useState<QuizResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [streamProgress, setStreamProgress] = useState<StreamProgress | null>(null);

  // Coaching state
  const [coachingQuestion, setCoachingQuestion] = useState<Question | null>(null);
  const [coachingUserAnswer, setCoachingUserAnswer] = useState("");
  const [coachingMessages, setCoachingMessages] = useState<ChatMessage[]>([]);
  const [coachingLoading, setCoachingLoading] = useState(false);

  // SSE cleanup ref — holds the close() function returned by generateQuizStream
  const streamCleanupRef = useRef<(() => void) | null>(null);

  const _handleSSEEvents = useCallback(
    (numQuestions: number) => (event: SSEEvent) => {
      switch (event.type) {
        case "start":
          setStreamProgress({ received: 0, total: event.total });
          break;

        case "question":
          setQuestions((prev) => [...prev, event.question]);
          setStreamProgress((prev) =>
            prev ? { ...prev, received: event.index + 1 } : { received: 1, total: numQuestions }
          );
          break;

        case "complete":
          setQuizId(event.quiz_id);
          setCurrentIndex(0);
          setAnswers([]);
          setCurrentFeedback(null);
          setStreamProgress(null);
          streamCleanupRef.current = null;
          setState("IN_PROGRESS");
          break;

        case "error":
          if (event.fatal) {
            setError(event.message);
            setStreamProgress(null);
            streamCleanupRef.current = null;
            setState("IDLE");
          }
          // Non-fatal batch errors: log but continue (partial results still arrive)
          break;
      }
    },
    []
  );

  const _handleSSEError = useCallback((err: Error) => {
    setError(err.message);
    setStreamProgress(null);
    streamCleanupRef.current = null;
    setState("IDLE");
  }, []);

  const startTopicQuiz = useCallback(
    (topic: string, numQuestions: number, questionTypes: string[]) => {
      setState("STREAMING");
      setError(null);
      setQuestions([]);
      setStreamProgress({ received: 0, total: numQuestions });

      const cleanup = generateQuizStream(
        { source_type: "topic", topic, num_questions: numQuestions, question_types: questionTypes },
        _handleSSEEvents(numQuestions),
        _handleSSEError,
      );
      streamCleanupRef.current = cleanup;
    },
    [_handleSSEEvents, _handleSSEError]
  );

  const startDocumentQuiz = useCallback(
    async (file: File, numQuestions: number, questionTypes: string[]) => {
      setState("GENERATING");
      setError(null);
      setQuestions([]);
      try {
        const upload = await uploadDocument(file);
        setState("STREAMING");
        setStreamProgress({ received: 0, total: numQuestions });

        const cleanup = generateQuizStream(
          {
            source_type: "document",
            document_id: upload.document_id,
            num_questions: numQuestions,
            question_types: questionTypes,
          },
          _handleSSEEvents(numQuestions),
          _handleSSEError,
        );
        streamCleanupRef.current = cleanup;
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to upload document");
        setState("IDLE");
      }
    },
    [_handleSSEEvents, _handleSSEError]
  );

  const cancelStream = useCallback(() => {
    if (streamCleanupRef.current) {
      streamCleanupRef.current();
      streamCleanupRef.current = null;
    }
    setStreamProgress(null);
    setState("IDLE");
  }, []);

  const submitCurrentAnswer = useCallback(
    async (answer: string) => {
      if (!quizId || currentIndex >= questions.length) return;
      const question = questions[currentIndex];
      setState("REVIEWING");
      try {
        const result = await submitAnswer(quizId, question.id, answer);
        setCurrentFeedback(result);
        setAnswers((prev) => [
          ...prev,
          { questionId: question.id, answer, result },
        ]);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to submit answer");
        setState("IN_PROGRESS");
      }
    },
    [quizId, currentIndex, questions]
  );

  const nextQuestion = useCallback(async () => {
    if (currentIndex + 1 >= questions.length) {
      // Quiz complete — fetch results
      setState("GENERATING");
      try {
        const res = await getQuizResults(quizId);
        setResults(res);
        setState("COMPLETE");
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to get results");
        setState("COMPLETE");
      }
    } else {
      setCurrentIndex((i) => i + 1);
      setCurrentFeedback(null);
      setState("IN_PROGRESS");
    }
  }, [currentIndex, questions.length, quizId]);

  const startCoaching = useCallback(
    (question: Question, userAnswer: string) => {
      setCoachingQuestion(question);
      setCoachingUserAnswer(userAnswer);
      setCoachingMessages([]);
      setState("COACHING");
    },
    []
  );

  const sendCoach = useCallback(
    async (message: string) => {
      if (!coachingQuestion) return;
      setCoachingLoading(true);
      const updatedMessages: ChatMessage[] = [
        ...coachingMessages,
        { role: "user", content: message },
      ];
      setCoachingMessages(updatedMessages);
      try {
        const res = await sendCoachMessage(
          coachingQuestion as unknown as Record<string, unknown>,
          coachingUserAnswer,
          updatedMessages,
          message
        );
        setCoachingMessages((prev) => [
          ...prev,
          { role: "assistant", content: res.response },
        ]);
      } catch {
        setCoachingMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "Sorry, I had trouble responding. Please try again.",
          },
        ]);
      }
      setCoachingLoading(false);
    },
    [coachingQuestion, coachingUserAnswer, coachingMessages]
  );

  const exitCoaching = useCallback(() => {
    setState("COMPLETE");
  }, []);

  const resetQuiz = useCallback(() => {
    if (streamCleanupRef.current) {
      streamCleanupRef.current();
      streamCleanupRef.current = null;
    }
    setState("IDLE");
    setQuizId("");
    setQuestions([]);
    setCurrentIndex(0);
    setAnswers([]);
    setCurrentFeedback(null);
    setResults(null);
    setError(null);
    setStreamProgress(null);
    setCoachingQuestion(null);
    setCoachingMessages([]);
  }, []);

  return {
    state,
    quizId,
    questions,
    currentIndex,
    currentQuestion: questions[currentIndex] ?? null,
    answers,
    currentFeedback,
    results,
    error,
    streamProgress,
    coachingQuestion,
    coachingMessages,
    coachingLoading,
    startTopicQuiz,
    startDocumentQuiz,
    cancelStream,
    submitCurrentAnswer,
    nextQuestion,
    startCoaching,
    sendCoach,
    exitCoaching,
    resetQuiz,
  };
}
