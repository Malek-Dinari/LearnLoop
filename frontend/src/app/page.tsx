"use client";

import { useState, useEffect } from "react";
import { useQuiz } from "@/hooks/useQuiz";
import TopicInput from "@/components/TopicInput";
import FileUpload from "@/components/FileUpload";
import QuizProgress from "@/components/QuizProgress";
import QuizCard from "@/components/QuizCard";
import ResultsSummary from "@/components/ResultsSummary";
import CoachingChat from "@/components/CoachingChat";
import FlashcardDeck from "@/components/FlashcardDeck";
import StudyChat from "@/components/StudyChat";
import { Loader2, Settings, BookOpen, Upload } from "lucide-react";
import { AuthUser, AUTH_CHANGE_EVENT, getUser } from "@/lib/auth";

type Tab = "topic" | "document";

const PAGE = "max-w-5xl mx-auto px-4 py-8";

export default function Home() {
  const quiz = useQuiz();
  const [tab, setTab] = useState<Tab>("topic");
  const [numQuestions, setNumQuestions] = useState(10);
  const [questionTypes, setQuestionTypes] = useState<string[]>(["mcq", "true_false", "short_answer"]);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);

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

  const toggleType = (t: string) => {
    setQuestionTypes((prev) =>
      prev.includes(t) ? (prev.length > 1 ? prev.filter((x) => x !== t) : prev) : [...prev, t]
    );
  };

  const handleStartTopic = (topic: string) => quiz.startTopicQuiz(topic, numQuestions, questionTypes);
  const handleStartDocument = () => { if (pendingFile) quiz.startDocumentQuiz(pendingFile, numQuestions, questionTypes); };

  // ─── GENERATING ───────────────────────────────────────────
  if (quiz.state === "GENERATING") {
    return (
      <div className={PAGE}>
        <div className="flex flex-col items-center justify-center py-32 space-y-4">
          <Loader2 size={48} className="animate-spin text-teal" />
          <p className="text-lg font-medium text-navy">Preparing your quiz…</p>
          <p className="text-sm text-gray-400">The AI is crafting your questions</p>
        </div>
      </div>
    );
  }

  // ─── STREAMING ────────────────────────────────────────────
  if (quiz.state === "STREAMING") {
    const received = quiz.streamProgress?.received ?? 0;
    const total = quiz.streamProgress?.total ?? 0;
    const pct = total > 0 ? Math.round((received / total) * 100) : 0;

    return (
      <div className={PAGE}>
        <div className="max-w-2xl mx-auto space-y-6 py-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Loader2 size={22} className="animate-spin text-teal flex-shrink-0" />
              <div>
                <p className="font-semibold text-navy text-sm">
                  Generating questions… {received} / {total || "?"}
                </p>
                <div className="w-56 bg-gray-200 rounded-full h-1.5 mt-1.5">
                  <div
                    className="bg-teal h-1.5 rounded-full transition-all duration-500"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            </div>
            <button onClick={quiz.cancelStream} className="text-xs text-gray-400 hover:text-coral transition-colors">
              Cancel
            </button>
          </div>

          {quiz.questions.length > 0 ? (
            <div className="space-y-3">
              {quiz.questions.map((q, i) => (
                <div key={q.id} className="card animate-fadeIn border border-gray-100">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-gray-400 font-medium">Q{i + 1}</span>
                    <div className="flex gap-2">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-teal/10 text-teal capitalize">{q.difficulty}</span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 capitalize">{q.type.replace("_", " ")}</span>
                    </div>
                  </div>
                  <p className="text-navy text-sm font-medium leading-snug">{q.question}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-sm text-gray-400 py-8">First questions arriving shortly…</p>
          )}
        </div>
      </div>
    );
  }

  // ─── QUIZ IN PROGRESS ─────────────────────────────────────
  if (quiz.state === "IN_PROGRESS" || quiz.state === "REVIEWING") {
    return (
      <div className={PAGE}>
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
      </div>
    );
  }

  // ─── RESULTS ──────────────────────────────────────────────
  if (quiz.state === "COMPLETE" && quiz.results) {
    return (
      <div className={PAGE}>
        <ResultsSummary
          results={quiz.results}
          onCoach={quiz.startCoaching}
          onNewQuiz={quiz.resetQuiz}
          onGenerateFlashcards={quiz.generateFlashcardsForQuiz}
          flashcardsLoading={quiz.flashcardsLoading}
        />
        {quiz.showFlashcards && quiz.flashcards.length > 0 && (
          <FlashcardDeck cards={quiz.flashcards} onClose={() => quiz.setShowFlashcards(false)} />
        )}
        <StudyChat messages={quiz.studyMessages} loading={quiz.studyLoading} onSend={quiz.sendStudyChat} quizActive={true} />
      </div>
    );
  }

  // ─── COACHING ─────────────────────────────────────────────
  if (quiz.state === "COACHING" && quiz.coachingQuestion) {
    return (
      <div className={PAGE}>
        {quiz.results && (
          <ResultsSummary
            results={quiz.results}
            onCoach={quiz.startCoaching}
            onNewQuiz={quiz.resetQuiz}
            onGenerateFlashcards={quiz.generateFlashcardsForQuiz}
            flashcardsLoading={quiz.flashcardsLoading}
          />
        )}
        {quiz.showFlashcards && quiz.flashcards.length > 0 && (
          <FlashcardDeck cards={quiz.flashcards} onClose={() => quiz.setShowFlashcards(false)} />
        )}
        <CoachingChat
          question={quiz.coachingQuestion}
          userAnswer={quiz.coachingMessages.length > 0 ? quiz.coachingMessages[0].content : ""}
          messages={quiz.coachingMessages}
          loading={quiz.coachingLoading}
          onSend={quiz.sendCoach}
          onClose={quiz.exitCoaching}
        />
      </div>
    );
  }

  // ─── IDLE — HOME ──────────────────────────────────────────
  return (
    <div className={`${PAGE} space-y-8`}>
      {/* Hero */}
      <div className="text-center space-y-4 pt-4 pb-2">
        <div className="flex justify-center">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/learnloop-logo-stacked.svg"
            alt="LearnLoop"
            style={{ height: "130px", width: "auto" }}
            className="drop-shadow-md"
          />
        </div>
        {user ? (
          <p className="text-base text-gray-500 max-w-lg mx-auto">
            Welcome back, <span className="font-semibold text-navy">{user.email.split("@")[0]}</span>. Ready to learn something new?
          </p>
        ) : (
          <p className="text-base text-gray-500 max-w-lg mx-auto">
            Upload a document or enter a topic to start learning with AI-generated quizzes and personalized coaching.
          </p>
        )}
      </div>

      {quiz.error && (
        <div className="max-w-2xl mx-auto bg-coral/10 border border-coral/30 text-coral px-4 py-3 rounded-xl text-sm">
          {quiz.error}
        </div>
      )}

      {/* Tab selector */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-xl max-w-sm mx-auto">
        <button
          onClick={() => setTab("topic")}
          className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-sm font-medium transition-all
            ${tab === "topic" ? "bg-white shadow text-navy" : "text-gray-500 hover:text-navy"}`}
        >
          <BookOpen size={15} /> Topic
        </button>
        <button
          onClick={() => setTab("document")}
          className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-sm font-medium transition-all
            ${tab === "document" ? "bg-white shadow text-navy" : "text-gray-500 hover:text-navy"}`}
        >
          <Upload size={15} /> Document
        </button>
      </div>

      {/* Input card */}
      <div className="card max-w-2xl mx-auto">
        {tab === "topic" ? (
          <TopicInput onSubmit={handleStartTopic} />
        ) : (
          <div className="space-y-4">
            <FileUpload onFileSelect={(f) => setPendingFile(f)} />
            <button onClick={handleStartDocument} disabled={!pendingFile} className="btn-primary w-full">
              Generate Quiz from Document
            </button>
          </div>
        )}
      </div>

      {/* Study chat assistant */}
      <StudyChat messages={quiz.studyMessages} loading={quiz.studyLoading} onSend={quiz.sendStudyChat} />

      {/* Quiz settings */}
      <div className="card max-w-2xl mx-auto">
        <div className="flex items-center gap-2 text-navy font-semibold mb-5">
          <Settings size={17} /> Quiz Settings
        </div>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-semibold text-navy mb-3">
              Questions: <span className="text-teal">{numQuestions}</span>
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
            <label className="block text-sm font-semibold text-navy mb-3">Question Types</label>
            <div className="space-y-2.5">
              {[
                { key: "mcq", label: "Multiple Choice" },
                { key: "true_false", label: "True / False" },
                { key: "short_answer", label: "Short Answer" },
              ].map(({ key, label }) => (
                <label key={key} className="flex items-center gap-2.5 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={questionTypes.includes(key)}
                    onChange={() => toggleType(key)}
                    className="w-4 h-4 rounded accent-teal cursor-pointer"
                  />
                  <span className="text-sm text-navy group-hover:text-teal transition-colors">{label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
