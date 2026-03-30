"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function QuizPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/");
  }, [router]);
  return (
    <p className="text-center text-gray-500 py-20">
      Redirecting to home...
    </p>
  );
}
