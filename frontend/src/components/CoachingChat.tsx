"use client";

import { useState, useRef, useEffect } from "react";
import { Question, ChatMessage } from "@/lib/types";
import { X, Send, Loader2 } from "lucide-react";
import clsx from "clsx";

interface Props {
  question: Question;
  userAnswer: string;
  messages: ChatMessage[];
  loading: boolean;
  onSend: (message: string) => void;
  onClose: () => void;
}

export default function CoachingChat({
  question,
  userAnswer,
  messages,
  loading,
  onSend,
  onClose,
}: Props) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || loading) return;
    onSend(input.trim());
    setInput("");
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex justify-end">
      <div className="w-full max-w-lg bg-white h-full flex flex-col shadow-2xl animate-in slide-in-from-right">
        {/* Header */}
        <div className="bg-navy text-white p-4 flex items-center justify-between">
          <div>
            <h3 className="font-semibold">AI Tutor</h3>
            <p className="text-xs text-gray-300">Socratic coaching mode</p>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-white/10 rounded">
            <X size={20} />
          </button>
        </div>

        {/* Question context */}
        <div className="px-4 py-3 bg-coral/5 border-b text-sm">
          <p className="font-medium text-navy">{question.question}</p>
          <p className="text-coral mt-1">Your answer: {userAnswer}</p>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <p className="text-center text-gray-400 text-sm mt-8">
              Ask about this question to get Socratic guidance.
              <br />
              Try: &quot;Why is my answer wrong?&quot; or &quot;Can you give me a hint?&quot;
            </p>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              className={clsx("flex", {
                "justify-end": msg.role === "user",
                "justify-start": msg.role === "assistant",
              })}
            >
              <div
                className={clsx("max-w-[80%] px-4 py-3 rounded-2xl text-sm", {
                  "bg-navy text-white rounded-br-md": msg.role === "user",
                  "bg-gray-100 text-navy rounded-bl-md": msg.role === "assistant",
                })}
              >
                {msg.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-bl-md">
                <Loader2 size={18} className="animate-spin text-gray-400" />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask the tutor..."
            className="flex-1 px-4 py-2 rounded-lg border-2 border-gray-200
                       focus:border-teal focus:outline-none text-sm"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="btn-primary px-4 py-2"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
