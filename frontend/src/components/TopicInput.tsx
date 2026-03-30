"use client";

import { useState } from "react";
import { BookOpen } from "lucide-react";

interface Props {
  onSubmit: (topic: string) => void;
  disabled?: boolean;
}

const SUGGESTIONS = [
  "Photosynthesis",
  "French Revolution",
  "Linear Algebra",
  "Python Decorators",
  "Human Anatomy",
  "World War II",
];

export default function TopicInput({ onSubmit, disabled }: Props) {
  const [topic, setTopic] = useState("");

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-navy font-semibold text-lg">
        <BookOpen size={20} />
        Enter a Topic
      </div>
      <div className="flex gap-3">
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && topic.trim()) onSubmit(topic.trim());
          }}
          placeholder="e.g., Photosynthesis, World War II, Python basics"
          className="flex-1 px-4 py-3 rounded-lg border-2 border-gray-200 focus:border-teal
                     focus:outline-none transition-colors text-navy"
          disabled={disabled}
        />
        <button
          onClick={() => topic.trim() && onSubmit(topic.trim())}
          disabled={!topic.trim() || disabled}
          className="btn-primary"
        >
          Go
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => {
              setTopic(s);
              onSubmit(s);
            }}
            disabled={disabled}
            className="px-3 py-1 text-sm bg-navy/5 text-navy rounded-full
                       hover:bg-navy/10 transition-colors disabled:opacity-50"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
