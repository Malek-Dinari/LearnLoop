"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AuthUser, clearSession, getUser } from "@/lib/auth";

export default function Nav() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const router = useRouter();

  useEffect(() => {
    setUser(getUser());
    const onStorage = () => setUser(getUser());
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const handleLogout = () => {
    clearSession();
    setUser(null);
    router.push("/");
  };

  return (
    <nav className="bg-navy text-white px-6 py-3">
      <div className="max-w-5xl mx-auto flex items-center justify-between">
        <Link href="/" className="flex items-center" aria-label="LearnLoop home">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/learnloop-logo-horizontal.svg"
            alt="LearnLoop"
            width={200}
            height={43}
            style={{ height: "43px", width: "auto" }}
          />
        </Link>
        <div className="flex items-center gap-4 text-sm">
          {user ? (
            <>
              {(user.role === "expert" || user.role === "admin") && (
                <Link href="/expert" className="text-gray-300 hover:text-white">
                  Expert
                </Link>
              )}
              <span className="text-gray-300 hidden sm:inline">{user.email}</span>
              <button
                onClick={handleLogout}
                className="px-3 py-1 rounded bg-white/10 hover:bg-white/20"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="text-gray-300 hover:text-white">
                Login
              </Link>
              <Link
                href="/signup"
                className="px-3 py-1 rounded bg-coral hover:bg-coral/90"
              >
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
