"use client";

import { useState } from "react";
import { Flashcard } from "@/lib/types";
import { ChevronLeft, ChevronRight, RotateCcw, X } from "lucide-react";
import clsx from "clsx";

interface Props {
  cards: Flashcard[];
  onClose: () => void;
}

export default function FlashcardDeck({ cards, onClose }: Props) {
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);

  if (cards.length === 0) return null;

  const card = cards[index];

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

        {/* Card counter + category */}
        <div className="flex items-center justify-between px-6 pt-4 text-sm">
          <span className="px-3 py-1 bg-teal/10 text-teal rounded-full font-medium text-xs">
            {card.category}
          </span>
          <span className="text-gray-400">
            {index + 1} / {cards.length}
          </span>
        </div>

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
