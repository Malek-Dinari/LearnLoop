"use client";

import { useState, useCallback } from "react";
import {
  Question,
  QuizState,
  AnswerResponse,
  QuizResults,
  ChatMessage,
} from "@/lib/types";
import {
  generateQuiz,
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

export function useQuiz() {
  const [state, setState] = useState<QuizState>("IDLE");
  const [quizId, setQuizId] = useState<string>("");
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<AnswerRecord[]>([]);
  const [currentFeedback, setCurrentFeedback] = useState<AnswerResponse | null>(null);
  const [results, setResults] = useState<QuizResults | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Coaching state
  const [coachingQuestion, setCoachingQuestion] = useState<Question | null>(null);
  const [coachingUserAnswer, setCoachingUserAnswer] = useState("");
  const [coachingMessages, setCoachingMessages] = useState<ChatMessage[]>([]);
  const [coachingLoading, setCoachingLoading] = useState(false);

  const startTopicQuiz = useCallback(
    async (topic: string, numQuestions: number, questionTypes: string[]) => {
      setState("GENERATING");
      setError(null);
      try {
        const res = await generateQuiz({
          source_type: "topic",
          topic,
          num_questions: numQuestions,
          question_types: questionTypes,
        });
        setQuizId(res.quiz_id);
        setQuestions(res.questions);
        setCurrentIndex(0);
        setAnswers([]);
        setCurrentFeedback(null);
        setState("IN_PROGRESS");
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to generate quiz");
        setState("IDLE");
      }
    },
    []
  );

  const startDocumentQuiz = useCallback(
    async (file: File, numQuestions: number, questionTypes: string[]) => {
      setState("GENERATING");
      setError(null);
      try {
        const upload = await uploadDocument(file);
        const res = await generateQuiz({
          source_type: "document",
          document_id: upload.document_id,
          num_questions: numQuestions,
          question_types: questionTypes,
        });
        setQuizId(res.quiz_id);
        setQuestions(res.questions);
        setCurrentIndex(0);
        setAnswers([]);
        setCurrentFeedback(null);
        setState("IN_PROGRESS");
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to generate quiz");
        setState("IDLE");
      }
    },
    []
  );

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
      } catch (e) {
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
    setState("IDLE");
    setQuizId("");
    setQuestions([]);
    setCurrentIndex(0);
    setAnswers([]);
    setCurrentFeedback(null);
    setResults(null);
    setError(null);
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
    coachingQuestion,
    coachingMessages,
    coachingLoading,
    startTopicQuiz,
    startDocumentQuiz,
    submitCurrentAnswer,
    nextQuestion,
    startCoaching,
    sendCoach,
    exitCoaching,
    resetQuiz,
  };
}
