"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { setSession, signup } from "@/lib/auth";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (password !== confirm) {
      setError("Passwords don't match");
      return;
    }
    setLoading(true);
    try {
      const resp = await signup(email, password);
      setSession(resp.access_token, resp.user);
      router.push("/");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Signup failed";
      if (msg.startsWith("409")) setError("Email already registered");
      else if (msg.startsWith("422")) setError("Invalid email or password");
      else setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 bg-white rounded-2xl shadow p-8">
      <h1 className="text-2xl font-semibold text-navy mb-6">Create account</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-4 py-2 rounded-lg border-2 border-gray-200 focus:border-teal focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            className="w-full px-4 py-2 rounded-lg border-2 border-gray-200 focus:border-teal focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Confirm password</label>
          <input
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            required
            className="w-full px-4 py-2 rounded-lg border-2 border-gray-200 focus:border-teal focus:outline-none"
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full btn-primary py-2 disabled:opacity-50"
        >
          {loading ? "Creating..." : "Sign up"}
        </button>
      </form>
      <p className="text-sm text-gray-600 mt-4">
        Already have an account?{" "}
        <Link href="/login" className="text-teal underline">
          Log in
        </Link>
      </p>
    </div>
  );
}
