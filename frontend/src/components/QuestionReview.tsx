"use client";

import { QuestionWithResult } from "@/lib/types";
import { CheckCircle, XCircle } from "lucide-react";

interface Props {
  questions: QuestionWithResult[];
}

export default function QuestionReview({ questions }: Props) {
  const correct = questions.filter((q) => q.is_correct).length;
  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-500">
        {correct} of {questions.length} correct
      </p>
      {questions.map((q, i) => (
        <div key={q.id} className="flex items-start gap-2 text-sm">
          {q.is_correct ? (
            <CheckCircle size={16} className="text-teal mt-0.5 shrink-0" />
          ) : (
            <XCircle size={16} className="text-coral mt-0.5 shrink-0" />
          )}
          <span className="text-navy/80">
            {i + 1}. {q.question}
          </span>
        </div>
      ))}
    </div>
  );
}
