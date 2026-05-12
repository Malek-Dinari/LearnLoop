"use client";

import { useState, useRef, useEffect } from "react";
import { ChatMessage } from "@/lib/types";
import { MessageCircle, X, Send, Loader2, GraduationCap, Volume2, VolumeX } from "lucide-react";
import clsx from "clsx";
import { useTTS } from "@/hooks/useTTS";

interface Props {
  messages: ChatMessage[];
  loading: boolean;
  onSend: (message: string) => void;
  quizActive?: boolean;
}

export default function StudyChat({ messages, loading, onSend, quizActive }: Props) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const { speak, stop, isSpeaking, isSupported: ttsSupported } = useTTS();
  const [speakingIdx, setSpeakingIdx] = useState<number | null>(null);

  useEffect(() => {
    return () => stop();
  }, [stop]);

  const toggleSpeak = (idx: number, text: string) => {
    if (speakingIdx === idx && isSpeaking) {
      stop();
      setSpeakingIdx(null);
    } else {
      speak(text);
      setSpeakingIdx(idx);
    }
  };

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  const handleSend = () => {
    if (!input.trim() || loading) return;
    onSend(input.trim());
    setInput("");
  };

  const unread = !open && messages.length > 0;

  return (
    <>
      {/* Floating button */}
      <button
        onClick={() => setOpen((o) => !o)}
        className={clsx(
          "fixed bottom-6 right-6 z-40 w-14 h-14 rounded-full shadow-lg flex items-center justify-center",
          "bg-navy text-white hover:bg-navy/90 transition-all",
          open && "rotate-90"
        )}
        aria-label="Study assistant"
      >
        {open ? <X size={22} /> : <MessageCircle size={22} />}
        {unread && (
          <span className="absolute top-0 right-0 w-3 h-3 bg-coral rounded-full border-2 border-white" />
        )}
      </button>

      {/* Chat panel */}
      {open && (
        <div className="fixed bottom-24 right-6 z-40 w-80 sm:w-96 bg-white rounded-2xl shadow-2xl
                        flex flex-col border border-gray-100 animate-in slide-in-from-bottom-4">
          {/* Header */}
          <div className="bg-navy text-white rounded-t-2xl px-4 py-3 flex items-center gap-3">
            <GraduationCap size={20} />
            <div>
              <p className="font-semibold text-sm">Study Assistant</p>
              <p className="text-xs text-gray-300">
                {quizActive ? "Quiz context active" : "Ask me anything"}
              </p>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 max-h-80">
            {messages.length === 0 && (
              <p className="text-center text-gray-400 text-xs mt-4">
                Ask any study question — I&apos;m here to help!
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
                  className={clsx("max-w-[85%] px-3 py-2 rounded-xl text-sm leading-relaxed", {
                    "bg-navy text-white rounded-br-sm": msg.role === "user",
                    "bg-gray-100 text-navy rounded-bl-sm": msg.role === "assistant",
                  })}
                >
                  {msg.content}
                  {msg.role === "assistant" && ttsSupported && (
                    <button
                      onClick={() => toggleSpeak(i, msg.content)}
                      className="ml-2 align-middle text-gray-500 hover:text-navy"
                      aria-label={speakingIdx === i && isSpeaking ? "Stop reading" : "Read aloud"}
                    >
                      {speakingIdx === i && isSpeaking ? <VolumeX size={12} /> : <Volume2 size={12} />}
                    </button>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 px-3 py-2 rounded-xl rounded-bl-sm">
                  <Loader2 size={14} className="animate-spin text-gray-400" />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="p-3 border-t flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask a question..."
              className="flex-1 px-3 py-2 rounded-lg border border-gray-200 text-sm
                         focus:border-teal focus:outline-none"
              disabled={loading}
              autoFocus
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="px-3 py-2 bg-navy text-white rounded-lg hover:bg-navy/90
                         disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              <Send size={15} />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
