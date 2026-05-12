import type { Metadata } from "next";
import "./globals.css";
import Nav from "@/components/Nav";

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
        <Nav />
        <main className="max-w-5xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
