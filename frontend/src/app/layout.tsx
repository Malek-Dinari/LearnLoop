import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LearnLoop - AI-Powered Study Platform",
  description:
    "Upload a document or enter a topic to start learning with AI-generated quizzes and personalized coaching.",
  icons: {
    icon: "/learnloop-favicon.png",
    apple: "/learnloop-icon-192.png",
  },
  manifest: "/manifest.json",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-warm-white">
        <nav className="bg-navy text-white px-6 py-3">
          <div className="max-w-5xl mx-auto flex items-center justify-between">
            <a href="/" className="flex items-center" aria-label="LearnLoop home">
              {/* Plain img for SVG — next/image cannot optimize vector formats */}
              <img
                src="/learnloop-logo-horizontal.svg"
                alt="LearnLoop"
                width={200}
                height={43}
                style={{ height: "43px", width: "auto" }}
              />
            </a>
            <span className="text-sm text-gray-400 hidden sm:block">
              AI-Powered Study Platform
            </span>
          </div>
        </nav>
        <main className="max-w-5xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
