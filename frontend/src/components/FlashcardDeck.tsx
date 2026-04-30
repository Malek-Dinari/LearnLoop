"use client";

import { useState, useEffect } from "react";
import { Flashcard } from "@/lib/types";
import { ChevronLeft, ChevronRight, RotateCcw, X, Volume2, VolumeX } from "lucide-react";
import clsx from "clsx";
import { useTTS } from "@/hooks/useTTS";

interface Props {
  cards: Flashcard[];
  onClose: () => void;
}

export default function FlashcardDeck({ cards, onClose }: Props) {
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const { speak, stop, isSpeaking, isSupported } = useTTS();

  // Stop speech when card changes
  useEffect(() => { stop(); }, [index]); // eslint-disable-line react-hooks/exhaustive-deps

  if (cards.length === 0) return null;

  const card = cards[index];

  // Build a stable question_id → quiz-question-number map (1-based, preserving first appearance)
  const qIndexMap = cards.reduce<Record<string, number>>((acc, c, i) => {
    if (c.question_id && !(c.question_id in acc)) {
      acc[c.question_id] = Object.keys(acc).length + 1;
    }
    return acc;
  }, {});
  const questionLabel = card.question_id ? `From Q${qIndexMap[card.question_id]}` : null;

  const prev = () => {
    setIndex((i) => Math.max(0, i - 1));
    setFlipped(false);
  };

  const next = () => {
    setIndex((i) => Math.min(cards.length - 1, i + 1));
    setFlipped(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === " " || e.key === "Enter") { e.preventDefault(); setFlipped((f) => !f); }
    if (e.key === "ArrowLeft") prev();
    if (e.key === "ArrowRight") next();
  };

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-xl flex flex-col"
        onKeyDown={handleKeyDown}
        tabIndex={0}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <div>
            <h3 className="font-bold text-navy text-lg">Flashcards</h3>
            <p className="text-xs text-gray-400">Space/click to flip · ← → to navigate</p>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg text-gray-400 hover:text-navy">
            <X size={20} />
          </button>
        </div>

        {/* Card counter + category + question link badge */}
        <div className="flex items-center justify-between px-6 pt-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 bg-teal/10 text-teal rounded-full font-medium text-xs">
              {card.category}
            </span>
            {questionLabel && (
              <span className="px-2 py-1 bg-amber-50 text-amber-600 border border-amber-200 rounded-full text-xs font-medium">
                {questionLabel}
              </span>
            )}
          </div>
          <span className="text-gray-400">
            {index + 1} / {cards.length}
          </span>
        </div>

        {/* TTS speaker button */}
        {isSupported && (
          <div className="flex justify-end px-6">
            <button
              onClick={() => isSpeaking ? stop() : speak(flipped ? card.back : card.front)}
              title={isSpeaking ? "Stop" : "Read aloud"}
              className="p-1.5 rounded-lg text-gray-400 hover:text-teal hover:bg-teal/10 transition-colors"
            >
              {isSpeaking ? <VolumeX size={16} /> : <Volume2 size={16} />}
            </button>
          </div>
        )}

        {/* Flip card */}
        <div className="px-6 py-6">
          <div
            className="relative cursor-pointer select-none"
            style={{ perspective: "1000px", height: "220px" }}
            onClick={() => setFlipped((f) => !f)}
          >
            {/* Front */}
            <div
              className={clsx(
                "absolute inset-0 rounded-xl border-2 border-gray-200 bg-gray-50 flex flex-col items-center justify-center p-6 text-center transition-all duration-500",
                flipped ? "opacity-0 rotate-y-180 pointer-events-none" : "opacity-100"
              )}
              style={{
                backfaceVisibility: "hidden",
                transform: flipped ? "rotateY(180deg)" : "rotateY(0deg)",
              }}
            >
              <p className="text-xs uppercase tracking-widest text-gray-400 mb-3">Question</p>
              <p className="text-navy font-semibold text-lg leading-snug">{card.front}</p>
              <p className="text-xs text-gray-400 mt-4">Click to reveal answer</p>
            </div>

            {/* Back */}
            <div
              className={clsx(
                "absolute inset-0 rounded-xl border-2 border-teal/40 bg-teal/5 flex flex-col items-center justify-center p-6 text-center transition-all duration-500",
                !flipped ? "opacity-0 pointer-events-none" : "opacity-100"
              )}
              style={{
                backfaceVisibility: "hidden",
                transform: flipped ? "rotateY(0deg)" : "rotateY(-180deg)",
              }}
            >
              <p className="text-xs uppercase tracking-widest text-teal mb-3">Answer</p>
              <p className="text-navy text-base leading-relaxed">{card.back}</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between px-6 pb-6 gap-4">
          <button
            onClick={prev}
            disabled={index === 0}
            className="flex items-center gap-1 px-4 py-2 rounded-lg border border-gray-200
                       text-sm font-medium text-navy hover:bg-gray-50 disabled:opacity-30
                       disabled:cursor-not-allowed transition-all"
          >
            <ChevronLeft size={16} /> Prev
          </button>

          <button
            onClick={() => setFlipped((f) => !f)}
            className="flex items-center gap-1 px-4 py-2 rounded-lg bg-navy/5
                       text-sm font-medium text-navy hover:bg-navy/10 transition-all"
          >
            <RotateCcw size={14} /> Flip
          </button>

          <button
            onClick={next}
            disabled={index === cards.length - 1}
            className="flex items-center gap-1 px-4 py-2 rounded-lg border border-gray-200
                       text-sm font-medium text-navy hover:bg-gray-50 disabled:opacity-30
                       disabled:cursor-not-allowed transition-all"
          >
            Next <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
