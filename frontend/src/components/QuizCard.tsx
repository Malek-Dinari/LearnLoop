"use client";

import { useState } from "react";
import { Question, AnswerResponse } from "@/lib/types";
import { CheckCircle, XCircle, ArrowRight } from "lucide-react";
import clsx from "clsx";

interface Props {
  question: Question;
  onSubmit: (answer: string) => void;
  feedback: AnswerResponse | null;
  onNext: () => void;
  isLast: boolean;
}

export default function QuizCard({ question, onSubmit, feedback, onNext, isLast }: Props) {
  const [selected, setSelected] = useState("");
  const [textAnswer, setTextAnswer] = useState("");
  const submitted = feedback !== null;

  const handleSubmit = () => {
    if (question.type === "short_answer") {
      if (textAnswer.trim()) onSubmit(textAnswer.trim());
    } else {
      if (selected) onSubmit(selected);
    }
  };

  const difficultyColor = {
    easy: "bg-teal/10 text-teal",
    medium: "bg-amber/20 text-amber",
    hard: "bg-coral/10 text-coral",
  }[question.difficulty] ?? "bg-gray-100 text-gray-600";

  return (
    <div className="card space-y-6">
      <div className="flex items-center justify-between">
        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${difficultyColor}`}>
          {question.difficulty}
        </span>
        <span className="text-xs text-gray-400 uppercase tracking-wide">
          {question.type === "mcq"
            ? "Multiple Choice"
            : question.type === "true_false"
            ? "True / False"
            : "Short Answer"}
        </span>
      </div>

      <h2 className="text-xl font-semibold text-navy leading-relaxed">
        {question.question}
      </h2>

      {/* Options */}
      {question.type !== "short_answer" && question.options && (
        <div className="space-y-3">
          {question.options.map((opt) => (
            <button
              key={opt}
              onClick={() => !submitted && setSelected(opt)}
              disabled={submitted}
              className={clsx(
                "w-full text-left px-5 py-4 rounded-lg border-2 transition-all font-medium",
                {
                  "border-gray-200 hover:border-teal/50": !submitted && selected !== opt,
                  "border-teal bg-teal/5": !submitted && selected === opt,
                  "border-teal bg-teal/10":
                    submitted && opt === feedback?.correct_answer,
                  "border-coral bg-coral/10":
                    submitted && selected === opt && !feedback?.is_correct,
                  "border-gray-100 text-gray-400":
                    submitted && opt !== feedback?.correct_answer && opt !== selected,
                }
              )}
            >
              {opt}
            </button>
          ))}
        </div>
      )}

      {question.type === "short_answer" && (
        <textarea
          value={textAnswer}
          onChange={(e) => setTextAnswer(e.target.value)}
          disabled={submitted}
          placeholder="Type your answer here..."
          rows={3}
          className="w-full px-4 py-3 rounded-lg border-2 border-gray-200
                     focus:border-teal focus:outline-none transition-colors resize-none"
        />
      )}

      {/* Feedback */}
      {feedback && (
        <div
          className={clsx("rounded-lg p-5 space-y-2 animate-in slide-in-from-bottom", {
            "bg-teal/10 border border-teal/30": feedback.is_correct,
            "bg-coral/10 border border-coral/30": !feedback.is_correct,
          })}
        >
          <div className="flex items-center gap-2 font-semibold">
            {feedback.is_correct ? (
              <>
                <CheckCircle size={20} className="text-teal" /> Correct!
              </>
            ) : (
              <>
                <XCircle size={20} className="text-coral" /> Incorrect
              </>
            )}
          </div>
          <p className="text-sm text-navy/80">{feedback.feedback}</p>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-end">
        {!submitted ? (
          <button
            onClick={handleSubmit}
            disabled={question.type === "short_answer" ? !textAnswer.trim() : !selected}
            className="btn-primary"
          >
            Submit Answer
          </button>
        ) : (
          <button onClick={onNext} className="btn-primary flex items-center gap-2">
            {isLast ? "See Results" : "Next Question"}
            <ArrowRight size={18} />
          </button>
        )}
      </div>
    </div>
  );
}
