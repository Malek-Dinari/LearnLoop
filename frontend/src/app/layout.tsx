import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LearnLoop - AI-Powered Study Platform",
  description: "Upload a document or enter a topic to start learning with AI-generated quizzes",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-warm-white">
        <nav className="bg-navy text-white px-6 py-4">
          <div className="max-w-5xl mx-auto flex items-center justify-between">
            <a href="/" className="text-2xl font-bold tracking-tight">
              <span className="text-teal">Learn</span>Loop
            </a>
            <span className="text-sm text-gray-400">AI-Powered Study Platform</span>
          </div>
        </nav>
        <main className="max-w-5xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
