"use client";

import { useState, useEffect, useCallback, useRef } from "react";

interface TTSOptions {
  rate?: number;   // 0.1–10, default 1
  pitch?: number;  // 0–2, default 1
  lang?: string;   // e.g. "en-US"
}

interface UseTTSReturn {
  speak: (text: string, opts?: TTSOptions) => void;
  stop: () => void;
  isSpeaking: boolean;
  isSupported: boolean;
}

export function useTTS(): UseTTSReturn {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    setIsSupported(typeof window !== "undefined" && "speechSynthesis" in window);
    return () => {
      // Stop speech on unmount
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const speak = useCallback((text: string, opts: TTSOptions = {}) => {
    if (!isSupported || !text.trim()) return;
    window.speechSynthesis.cancel();

    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = opts.rate ?? 1;
    utter.pitch = opts.pitch ?? 1;
    utter.lang = opts.lang ?? "en-US";

    // Pick the best available English voice (prefer Natural/Premium/Google)
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(
      (v) =>
        v.lang.startsWith("en") &&
        (v.name.includes("Natural") || v.name.includes("Premium") || v.name.includes("Google"))
    ) ?? voices.find((v) => v.lang.startsWith("en"));
    if (preferred) utter.voice = preferred;

    utter.onstart = () => setIsSpeaking(true);
    utter.onend = () => setIsSpeaking(false);
    utter.onerror = () => setIsSpeaking(false);

    utteranceRef.current = utter;
    window.speechSynthesis.speak(utter);
  }, [isSupported]);

  const stop = useCallback(() => {
    if (!isSupported) return;
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  }, [isSupported]);

  return { speak, stop, isSpeaking, isSupported };
}
