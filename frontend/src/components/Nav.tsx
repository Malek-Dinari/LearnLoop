"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { AuthUser, AUTH_CHANGE_EVENT, clearSession, getUser } from "@/lib/auth";
import { LogOut, GraduationCap, ChevronDown } from "lucide-react";

export default function Nav() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const sync = () => setUser(getUser());
    sync();
    window.addEventListener(AUTH_CHANGE_EVENT, sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener(AUTH_CHANGE_EVENT, sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  // Close dropdown on route change
  useEffect(() => setMenuOpen(false), [pathname]);

  const handleLogout = () => {
    clearSession();
    setMenuOpen(false);
    router.push("/");
  };

  const initials = user?.email
    ? user.email.slice(0, 2).toUpperCase()
    : "";

  return (
    <header className="bg-navy border-b border-white/10 sticky top-0 z-50">
      <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center" aria-label="LearnLoop home">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/learnloop-logo-horizontal.svg"
            alt="LearnLoop"
            style={{ height: "38px", width: "auto" }}
          />
        </Link>

        {/* Right side */}
        <div className="flex items-center gap-3">
          {user ? (
            <div className="relative">
              <button
                onClick={() => setMenuOpen((o) => !o)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 transition-colors text-white text-sm"
              >
                <span className="w-7 h-7 rounded-full bg-teal text-navy text-xs font-bold flex items-center justify-center flex-shrink-0">
                  {initials}
                </span>
                <span className="hidden sm:block max-w-[140px] truncate">{user.email}</span>
                <ChevronDown size={14} className={`transition-transform ${menuOpen ? "rotate-180" : ""}`} />
              </button>

              {menuOpen && (
                <div className="absolute right-0 mt-2 w-52 bg-white rounded-xl shadow-xl border border-gray-100 overflow-hidden animate-fadeIn">
                  <div className="px-4 py-3 border-b border-gray-100">
                    <p className="text-xs text-gray-400">Signed in as</p>
                    <p className="text-sm font-semibold text-navy truncate">{user.email}</p>
                    <span className="inline-block mt-1 text-xs px-2 py-0.5 rounded-full bg-navy/10 text-navy font-medium capitalize">
                      {user.role}
                    </span>
                  </div>
                  {(user.role === "expert" || user.role === "admin") && (
                    <Link
                      href="/expert"
                      className="flex items-center gap-2 px-4 py-2.5 text-sm text-navy hover:bg-gray-50 transition-colors"
                    >
                      <GraduationCap size={15} />
                      Expert Console
                    </Link>
                  )}
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-coral hover:bg-coral/5 transition-colors"
                  >
                    <LogOut size={15} />
                    Log out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
              <Link
                href="/login"
                className="text-sm text-gray-300 hover:text-white transition-colors"
              >
                Log in
              </Link>
              <Link
                href="/signup"
                className="text-sm px-4 py-1.5 rounded-lg bg-teal text-navy font-semibold hover:bg-teal/90 transition-colors"
              >
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>

      {/* Click-outside overlay */}
      {menuOpen && (
        <div
          className="fixed inset-0 z-[-1]"
          onClick={() => setMenuOpen(false)}
        />
      )}
    </header>
  );
}
