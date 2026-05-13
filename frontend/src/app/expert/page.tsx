"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { authFetch, getUser } from "@/lib/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

interface Correction {
  id: string;
  original_question: Record<string, unknown> | null;
  corrected_question: Record<string, unknown>;
  topic_tags: string[];
  expert_id: string;
  approved: boolean;
  created_at: string;
}

const PLACEHOLDER = JSON.stringify(
  {
    type: "mcq",
    question: "What is photosynthesis?",
    options: ["A", "B", "C", "D"],
    correct_answer: "A",
    explanation: "Why A is correct.",
    difficulty: "easy",
  },
  null,
  2,
);

export default function ExpertPage() {
  const router = useRouter();
  const [role, setRole] = useState<string | null>(null);
  const [json, setJson] = useState(PLACEHOLDER);
  const [tags, setTags] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [mine, setMine] = useState<Correction[]>([]);
  const [pending, setPending] = useState<Correction[]>([]);

  useEffect(() => {
    const user = getUser();
    if (!user) {
      router.push("/login");
      return;
    }
    if (user.role !== "expert" && user.role !== "admin") {
      router.push("/");
      return;
    }
    setRole(user.role);
  }, [router]);

  const loadMine = useCallback(async () => {
    try {
      const res = await authFetch(`${API_BASE}/expert/corrections?approved=false`);
      if (res.ok) setMine(await res.json());
    } catch { /* ignore */ }
  }, []);

  const loadPending = useCallback(async () => {
    if (role !== "admin") return;
    try {
      const res = await authFetch(`${API_BASE}/expert/corrections?approved=false`);
      if (res.ok) setPending(await res.json());
    } catch { /* ignore */ }
  }, [role]);

  useEffect(() => {
    if (!role) return;
    loadMine();
    loadPending();
  }, [role, loadMine, loadPending]);

  const handleSubmit = async () => {
    setError(null);
    setSubmitting(true);
    try {
      const corrected = JSON.parse(json);
      const tagList = tags
        .split(",")
        .map((t) => t.trim().toLowerCase())
        .filter(Boolean);
      const res = await authFetch(`${API_BASE}/expert/corrections`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          corrected_question: corrected,
          topic_tags: tagList,
          original_question: null,
        }),
      });
      if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
      setJson(PLACEHOLDER);
      setTags("");
      await loadMine();
      await loadPending();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submit failed");
    } finally {
      setSubmitting(false);
    }
  };

  const approve = async (id: string) => {
    try {
      const res = await authFetch(`${API_BASE}/expert/corrections/${id}/approve`, {
        method: "PATCH",
      });
      if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
      await loadPending();
      await loadMine();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approve failed");
    }
  };

  if (!role) {
    return <p className="text-center text-gray-500">Loading...</p>;
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      <h1 className="text-3xl font-semibold text-navy">Expert Console</h1>
      <p className="text-sm text-gray-600">
        Submit corrections that future quizzes will reference. Admins approve
        before they are injected into generation.
      </p>

      <section className="card space-y-4">
        <h2 className="text-xl font-medium text-navy">Submit a correction</h2>
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Corrected question (JSON)</span>
          <textarea
            value={json}
            onChange={(e) => setJson(e.target.value)}
            rows={12}
            className="w-full mt-1 px-3 py-2 rounded-lg border-2 border-gray-200 font-mono text-xs focus:border-teal focus:outline-none"
          />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Topic tags (comma-separated)</span>
          <input
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="photosynthesis, biology, plants"
            className="w-full mt-1 px-3 py-2 rounded-lg border-2 border-gray-200 focus:border-teal focus:outline-none"
          />
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          onClick={handleSubmit}
          disabled={submitting}
          className="btn-primary px-4 py-2 disabled:opacity-50"
        >
          {submitting ? "Submitting..." : "Submit"}
        </button>
      </section>

      <section className="card space-y-3">
        <h2 className="text-xl font-medium text-navy">My pending corrections</h2>
        {mine.length === 0 ? (
          <p className="text-sm text-gray-500">None.</p>
        ) : (
          <ul className="space-y-2">
            {mine.map((c) => (
              <li key={c.id} className="border rounded p-3 text-sm">
                <p className="font-medium">
                  {String((c.corrected_question as Record<string, unknown>).question ?? "(no question)")}
                </p>
                <p className="text-xs text-gray-500">
                  Tags: {c.topic_tags.join(", ") || "(none)"} • Approved: {c.approved ? "yes" : "no"}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>

      {role === "admin" && (
        <section className="card space-y-3">
          <h2 className="text-xl font-medium text-navy">Admin: pending approvals</h2>
          {pending.length === 0 ? (
            <p className="text-sm text-gray-500">Nothing waiting.</p>
          ) : (
            <ul className="space-y-2">
              {pending.map((c) => (
                <li key={c.id} className="border rounded p-3 text-sm flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <p className="font-medium">
                      {String((c.corrected_question as Record<string, unknown>).question ?? "(no question)")}
                    </p>
                    <p className="text-xs text-gray-500">
                      Tags: {c.topic_tags.join(", ") || "(none)"}
                    </p>
                  </div>
                  <button
                    onClick={() => approve(c.id)}
                    className="px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-700 text-white text-xs"
                  >
                    Approve
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  );
}
