"use client";

import { useState } from "react";
import { useQuiz } from "@/hooks/useQuiz";
import TopicInput from "@/components/TopicInput";
import FileUpload from "@/components/FileUpload";
import QuizProgress from "@/components/QuizProgress";
import QuizCard from "@/components/QuizCard";
import ResultsSummary from "@/components/ResultsSummary";
import CoachingChat from "@/components/CoachingChat";
import { Loader2, Settings, BookOpen, Upload } from "lucide-react";

type Tab = "topic" | "document";

export default function Home() {
  const quiz = useQuiz();
  const [tab, setTab] = useState<Tab>("topic");
  const [numQuestions, setNumQuestions] = useState(10);
  const [questionTypes, setQuestionTypes] = useState<string[]>([
    "mcq",
    "true_false",
    "short_answer",
  ]);
  const [pendingFile, setPendingFile] = useState<File | null>(null);

  const toggleType = (t: string) => {
    setQuestionTypes((prev) =>
      prev.includes(t) ? (prev.length > 1 ? prev.filter((x) => x !== t) : prev) : [...prev, t]
    );
  };

  const handleStartTopic = (topic: string) => {
    quiz.startTopicQuiz(topic, numQuestions, questionTypes);
  };

  const handleStartDocument = () => {
    if (pendingFile) {
      quiz.startDocumentQuiz(pendingFile, numQuestions, questionTypes);
    }
  };

  // ─── GENERATING ────────────────────────────────────────────
  if (quiz.state === "GENERATING") {
    return (
      <div className="flex flex-col items-center justify-center py-32 space-y-4">
        <Loader2 size={48} className="animate-spin text-teal" />
        <p className="text-lg font-medium text-navy">Generating your quiz...</p>
        <p className="text-sm text-gray-400">This may take a moment while the AI crafts questions</p>
      </div>
    );
  }

  // ─── QUIZ IN PROGRESS / REVIEWING ─────────────────────────
  if (quiz.state === "IN_PROGRESS" || quiz.state === "REVIEWING") {
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <QuizProgress current={quiz.currentIndex} total={quiz.questions.length} />
        {quiz.currentQuestion && (
          <QuizCard
            key={quiz.currentQuestion.id}
            question={quiz.currentQuestion}
            onSubmit={quiz.submitCurrentAnswer}
            feedback={quiz.currentFeedback}
            onNext={quiz.nextQuestion}
            isLast={quiz.currentIndex === quiz.questions.length - 1}
          />
        )}
      </div>
    );
  }

  // ─── RESULTS ───────────────────────────────────────────────
  if (quiz.state === "COMPLETE" && quiz.results) {
    return (
      <>
        <ResultsSummary
          results={quiz.results}
          onCoach={quiz.startCoaching}
          onNewQuiz={quiz.resetQuiz}
        />
        {quiz.state === "COMPLETE" && quiz.coachingQuestion && null}
      </>
    );
  }

  // ─── COACHING ──────────────────────────────────────────────
  if (quiz.state === "COACHING" && quiz.coachingQuestion) {
    return (
      <>
        {quiz.results && (
          <ResultsSummary
            results={quiz.results}
            onCoach={quiz.startCoaching}
            onNewQuiz={quiz.resetQuiz}
          />
        )}
        <CoachingChat
          question={quiz.coachingQuestion}
          userAnswer={quiz.coachingMessages.length > 0 ? quiz.coachingMessages[0].content : ""}
          messages={quiz.coachingMessages}
          loading={quiz.coachingLoading}
          onSend={quiz.sendCoach}
          onClose={quiz.exitCoaching}
        />
      </>
    );
  }

  // ─── IDLE — HOME PAGE ──────────────────────────────────────
  return (
    <div className="space-y-10">
      {/* Hero */}
      <div className="text-center space-y-4 py-8">
        <div className="flex justify-center">
          <img
            src="/learnloop-logo-stacked.svg"
            alt="LearnLoop"
            width={220}
            height={147}
            style={{ height: "147px", width: "auto" }}
            className="drop-shadow-md"
          />
        </div>
        <p className="text-lg text-gray-500 max-w-xl mx-auto">
          Upload a document or enter a topic to start learning with AI-generated quizzes
          and personalized coaching.
        </p>
      </div>

      {quiz.error && (
        <div className="bg-coral/10 border border-coral/30 text-coral px-4 py-3 rounded-lg text-sm">
          {quiz.error}
        </div>
      )}

      {/* Tab selector */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-lg max-w-md mx-auto">
        <button
          onClick={() => setTab("topic")}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-md text-sm font-medium transition-all
            ${tab === "topic" ? "bg-white shadow text-navy" : "text-gray-500 hover:text-navy"}`}
        >
          <BookOpen size={16} /> Enter a Topic
        </button>
        <button
          onClick={() => setTab("document")}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-md text-sm font-medium transition-all
            ${tab === "document" ? "bg-white shadow text-navy" : "text-gray-500 hover:text-navy"}`}
        >
          <Upload size={16} /> Upload Document
        </button>
      </div>

      {/* Input area */}
      <div className="card max-w-2xl mx-auto">
        {tab === "topic" ? (
          <TopicInput onSubmit={handleStartTopic} />
        ) : (
          <div className="space-y-4">
            <FileUpload onFileSelect={(f) => setPendingFile(f)} />
            <button
              onClick={handleStartDocument}
              disabled={!pendingFile}
              className="btn-primary w-full"
            >
              Generate Quiz from Document
            </button>
          </div>
        )}
      </div>

      {/* Settings */}
      <div className="card max-w-2xl mx-auto">
        <div className="flex items-center gap-2 text-navy font-semibold mb-4">
          <Settings size={18} /> Quiz Settings
        </div>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-navy mb-2">
              Number of Questions: {numQuestions}
            </label>
            <input
              type="range"
              min={2}
              max={50}
              value={numQuestions}
              onChange={(e) => setNumQuestions(Number(e.target.value))}
              className="w-full accent-teal"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>2</span>
              <span>50</span>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-navy mb-2">
              Question Types
            </label>
            <div className="space-y-2">
              {[
                { key: "mcq", label: "Multiple Choice" },
                { key: "true_false", label: "True / False" },
                { key: "short_answer", label: "Short Answer" },
              ].map(({ key, label }) => (
                <label key={key} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={questionTypes.includes(key)}
                    onChange={() => toggleType(key)}
                    className="rounded accent-teal"
                  />
                  <span className="text-sm text-navy">{label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
