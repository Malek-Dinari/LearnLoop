"use client";

interface Props {
  current: number;
  total: number;
}

export default function QuizProgress({ current, total }: Props) {
  const pct = ((current + 1) / total) * 100;
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm font-medium text-navy">
        <span>Question {current + 1} of {total}</span>
        <span>{Math.round(pct)}%</span>
      </div>
      <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-teal rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
