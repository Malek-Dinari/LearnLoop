"use client";

import { QuizResults, Question } from "@/lib/types";
import { CheckCircle, XCircle, MessageCircle } from "lucide-react";
import clsx from "clsx";

interface Props {
  results: QuizResults;
  onCoach: (question: Question, userAnswer: string) => void;
  onNewQuiz: () => void;
}

export default function ResultsSummary({ results, onCoach, onNewQuiz }: Props) {
  const pct = results.percentage;
  const color = pct >= 70 ? "text-teal" : pct >= 40 ? "text-amber" : "text-coral";

  return (
    <div className="space-y-8">
      {/* Score header */}
      <div className="card text-center space-y-4">
        <h2 className="text-3xl font-bold text-navy">Quiz Complete!</h2>
        <div className={clsx("text-6xl font-extrabold", color)}>
          {results.score}/{results.total}
        </div>
        <p className="text-lg text-gray-500">{pct.toFixed(0)}% correct</p>
        <div className="flex justify-center gap-6 text-sm">
          {Object.entries(results.per_type).map(([type, score]) => (
            <div key={type} className="text-center">
              <div className="font-semibold text-navy">{score}</div>
              <div className="text-gray-400">
                {type === "mcq" ? "MCQ" : type === "true_false" ? "T/F" : "Short"}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Coaching message */}
      <div className="card">
        <h3 className="font-semibold text-navy mb-3">AI Coach Feedback</h3>
        <div className="prose prose-sm max-w-none text-navy/80 whitespace-pre-line">
          {results.coaching_message}
        </div>
        {results.weak_areas.length > 0 && (
          <div className="mt-4">
            <p className="text-sm font-semibold text-navy mb-2">Areas to review:</p>
            <div className="flex flex-wrap gap-2">
              {results.weak_areas.map((area, i) => (
                <span
                  key={i}
                  className="px-3 py-1 bg-amber/10 text-amber rounded-full text-sm font-medium"
                >
                  {area}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Question review */}
      <div className="space-y-4">
        <h3 className="font-semibold text-navy text-lg">Question Review</h3>
        {results.questions_with_results.map((q, i) => (
          <div
            key={q.id}
            className={clsx("card flex gap-4", {
              "border-l-4 border-teal": q.is_correct,
              "border-l-4 border-coral": !q.is_correct,
            })}
          >
            <div className="pt-1">
              {q.is_correct ? (
                <CheckCircle size={20} className="text-teal" />
              ) : (
                <XCircle size={20} className="text-coral" />
              )}
            </div>
            <div className="flex-1 space-y-1">
              <p className="font-medium text-navy">
                {i + 1}. {q.question}
              </p>
              <p className="text-sm text-gray-500">
                Your answer: <span className="font-medium">{q.user_answer || "(none)"}</span>
              </p>
              {!q.is_correct && (
                <>
                  <p className="text-sm text-teal">
                    Correct: <span className="font-medium">{q.correct_answer}</span>
                  </p>
                  <button
                    onClick={() => onCoach(q, q.user_answer)}
                    className="mt-2 inline-flex items-center gap-1 text-sm font-medium
                               text-navy hover:text-teal transition-colors"
                  >
                    <MessageCircle size={16} /> Ask the Tutor
                  </button>
                </>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="text-center">
        <button onClick={onNewQuiz} className="btn-secondary">
          Start New Quiz
        </button>
      </div>
    </div>
  );
}
