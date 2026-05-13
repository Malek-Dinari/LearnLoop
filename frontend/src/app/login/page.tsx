"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, LogIn } from "lucide-react";
import { login, setSession } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const resp = await login(email, password);
      setSession(resp.access_token, resp.user);
      router.push("/");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Login failed";
      if (msg.startsWith("401")) setError("Wrong email or password.");
      else setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-56px)] flex">
      {/* Brand panel */}
      <div className="hidden lg:flex flex-col justify-center items-center w-2/5 bg-navy px-12 py-16 space-y-8">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/learnloop-logo-stacked.svg"
          alt="LearnLoop"
          style={{ height: "140px", width: "auto" }}
          className="drop-shadow-lg"
        />
        <div className="text-center space-y-3 max-w-xs">
          <h2 className="text-white text-2xl font-bold leading-snug">
            Learn smarter, not harder.
          </h2>
          <p className="text-gray-400 text-sm leading-relaxed">
            AI-generated quizzes, personalized coaching, and expert-verified content
            — all in one place.
          </p>
        </div>
        <div className="flex flex-col gap-3 w-full max-w-xs">
          {["Adaptive quizzes from any topic", "Expert-verified questions", "AI coaching & flashcards"].map((f) => (
            <div key={f} className="flex items-center gap-3">
              <span className="w-5 h-5 rounded-full bg-teal/20 border border-teal/40 flex items-center justify-center flex-shrink-0">
                <span className="w-2 h-2 rounded-full bg-teal" />
              </span>
              <span className="text-gray-300 text-sm">{f}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Form panel */}
      <div className="flex-1 flex items-center justify-center px-6 py-12 bg-warm-white">
        <div className="w-full max-w-md space-y-8">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold text-navy">Welcome back</h1>
            <p className="text-gray-500 text-sm">Sign in to continue learning.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-1.5">
              <label className="block text-sm font-semibold text-navy">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                placeholder="you@example.com"
                className="w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-teal focus:outline-none transition-colors bg-white text-navy placeholder-gray-400"
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-semibold text-navy">Password</label>
              <div className="relative">
                <input
                  type={showPwd ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className="w-full px-4 py-3 pr-12 rounded-xl border-2 border-gray-200 focus:border-teal focus:outline-none transition-colors bg-white text-navy placeholder-gray-400"
                />
                <button
                  type="button"
                  onClick={() => setShowPwd((s) => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-navy transition-colors p-1"
                  tabIndex={-1}
                >
                  {showPwd ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            {error && (
              <div className="flex items-start gap-2 bg-coral/10 border border-coral/30 text-coral rounded-lg px-4 py-3 text-sm">
                <span className="mt-0.5 flex-shrink-0">⚠</span>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 btn-primary py-3 text-base"
            >
              {loading ? (
                <span className="w-5 h-5 border-2 border-navy/30 border-t-navy rounded-full animate-spin" />
              ) : (
                <LogIn size={18} />
              )}
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500">
            Don&apos;t have an account?{" "}
            <Link href="/signup" className="text-teal font-semibold hover:underline">
              Create one free
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
