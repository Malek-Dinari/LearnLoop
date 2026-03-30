GRADING_SYSTEM = (
    "You are grading a student's short answer. Be fair but accurate. "
    "Award partial credit for answers that show understanding even if not perfectly worded."
)

GRADING_USER = """Question: {question}
Correct answer: {correct_answer}
Student's answer: {user_answer}

Grade this answer. Respond with ONLY a JSON object:
{{
  "score": 0 or 0.5 or 1,
  "is_correct": true or false,
  "feedback": "specific feedback on their answer"
}}

Score guide:
- 1.0 = correct or essentially correct
- 0.5 = partially correct, shows some understanding
- 0.0 = incorrect or irrelevant"""

SUMMARY_SYSTEM = (
    "You are a supportive educational coach. Analyze the student's quiz performance "
    "and provide encouraging, specific feedback. Identify their strengths and areas to improve."
)

SUMMARY_USER = """The student just completed a quiz. Here are their results:

Score: {score}/{total} ({percentage:.0f}%)

Performance by question type:
{per_type_summary}

Questions they got wrong:
{wrong_questions}

Provide a personalized coaching message (2-3 paragraphs) that:
1. Acknowledges what they did well
2. Identifies specific areas to improve
3. Gives concrete study suggestions

Also list 2-4 specific weak areas/topics they should review.

Respond with ONLY a JSON object:
{{
  "coaching_message": "your coaching message here",
  "weak_areas": ["area 1", "area 2"]
}}"""
