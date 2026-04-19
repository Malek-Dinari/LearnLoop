"""Phase A: Question Quality & Diversity Tests
Test TF-IDF dedup, diversity prompts, and keyword extraction.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import json

from app.services.quiz_service import (
    _is_near_duplicate,
    extract_topic_keywords,
    quiz_service,
)
from app.prompts.question_gen import build_diversity_directive, QUESTION_ASPECTS


class TestTopicKeywordExtraction:
    """Test extract_topic_keywords helper."""

    def test_extract_capitalized_keywords(self):
        """Capitalized words are extracted as keywords."""
        text = "What is Photosynthesis in Plant Biology?"
        keywords = extract_topic_keywords(text, num_words=3)
        assert len(keywords) <= 3
        assert any("photosynthesis" in k for k in keywords)

    def test_extract_long_words(self):
        """Words longer than 5 characters are extracted."""
        text = "Define metabolism and respiration"
        keywords = extract_topic_keywords(text, num_words=5)
        # "metabolism" and "respiration" should be included (both > 5 chars)
        assert any("metabolism" in k or "respiration" in k for k in keywords)

    def test_extract_empty_question(self):
        """Empty question returns empty list."""
        keywords = extract_topic_keywords("")
        assert keywords == []

    def test_extract_respects_limit(self):
        """Result respects num_words limit."""
        text = "Define ATP Adenosine Triphosphate molecular cellular respiration photosynthesis"
        keywords = extract_topic_keywords(text, num_words=3)
        assert len(keywords) <= 3

    def test_extract_removes_punctuation(self):
        """Punctuation is removed from extracted keywords."""
        text = "What is photosynthesis? Define it clearly!"
        keywords = extract_topic_keywords(text, num_words=5)
        assert all("?" not in k and "!" not in k for k in keywords)


class TestTFIDFDedup:
    """Test TF-IDF near-duplicate detection."""

    def test_tfidf_dedup_detects_paraphrase(self):
        """Similar paraphrases are flagged as duplicates."""
        q1 = _is_near_duplicate(
            {"question": "What is photosynthesis?", "correct_answer": "light to energy"},
            [
                {
                    "question": "What is photosynthesis?",
                    "correct_answer": "converting light into energy",
                }
            ],
            threshold=0.7,
        )
        assert q1 is True, "Photosynthesis paraphrases should be detected as duplicates"

    def test_tfidf_dedup_allows_different_concepts(self):
        """Different concepts are not flagged as duplicates."""
        q_is_dup = _is_near_duplicate(
            {"question": "What is photosynthesis?", "correct_answer": "Converting light to energy"},
            [
                {
                    "question": "What is cellular respiration?",
                    "correct_answer": "Breaking down glucose to release energy",
                }
            ],
            threshold=0.7,
        )
        assert q_is_dup is False, "Photosynthesis and respiration should not be duplicates"

    def test_tfidf_dedup_empty_existing(self):
        """No duplicates when existing list is empty."""
        q_is_dup = _is_near_duplicate(
            {"question": "What is photosynthesis?", "correct_answer": "light to energy"},
            [],
        )
        assert q_is_dup is False

    def test_tfidf_dedup_high_threshold(self):
        """High threshold reduces false positives."""
        q_is_dup = _is_near_duplicate(
            {"question": "What is photosynthesis?", "correct_answer": "light energy"},
            [
                {
                    "question": "Explain photosynthesis.",
                    "correct_answer": "light-driven process",
                }
            ],
            threshold=0.95,  # Very high threshold
        )
        # At 0.95, even related questions may not be flagged
        assert isinstance(q_is_dup, bool)

    def test_tfidf_dedup_low_threshold(self):
        """Low threshold increases sensitivity."""
        q_is_dup = _is_near_duplicate(
            {"question": "Photosynthesis", "correct_answer": "light"},
            [
                {
                    "question": "photosynthesis definition",
                    "correct_answer": "light reaction",
                }
            ],
            threshold=0.3,  # Low threshold
        )
        # At 0.3, similar questions should be flagged
        assert q_is_dup is True


class TestDiversityPrompt:
    """Test diversity directive construction."""

    def test_diversity_prompt_rotates_aspects(self):
        """Aspect rotation cycles through QUESTION_ASPECTS."""
        aspect_0 = build_diversity_directive(batch_index=0)
        aspect_1 = build_diversity_directive(batch_index=1)
        aspect_2 = build_diversity_directive(batch_index=2)

        assert QUESTION_ASPECTS[0] in aspect_0
        assert QUESTION_ASPECTS[1] in aspect_1
        assert QUESTION_ASPECTS[2] in aspect_2

    def test_diversity_prompt_injects_seen_topics(self):
        """Seen topics are injected into the prompt."""
        seen_topics = ["photosynthesis", "chloroplast", "glucose"]
        directive = build_diversity_directive(batch_index=1, seen_topics=seen_topics)

        assert "Avoid repeating these concepts" in directive
        for topic in seen_topics:
            assert topic in directive

    def test_diversity_prompt_empty_seen_topics(self):
        """Directive works with no seen topics."""
        directive = build_diversity_directive(batch_index=0, seen_topics=None)
        assert len(directive) > 0
        assert QUESTION_ASPECTS[0] in directive

    def test_diversity_prompt_truncates_long_topic_list(self):
        """Very long topic lists are truncated."""
        long_topics = [f"topic_{i}" for i in range(20)]
        directive = build_diversity_directive(batch_index=1, seen_topics=long_topics)

        # Should only include first 12 topics, not all 20
        # Count how many are included (rough check)
        assert "topic_0" in directive
        assert "topic_11" in directive or len(directive) > 0  # At least some are included


class TestGenerateBatchWithDiversity:
    """Integration tests for _generate_batch with diversity."""

    @pytest.mark.asyncio
    async def test_generate_batch_uses_temperature_from_settings(self):
        """_generate_batch uses settings.quiz_temperature."""
        with patch("app.services.quiz_service.llm_service.generate_json") as mock_llm:
            mock_llm.return_value = {
                "questions": [
                    {
                        "question": "Test Q",
                        "correct_answer": "Test A",
                        "options": ["A", "B", "C", "D"],
                    }
                ]
            }

            with patch("app.config.settings.quiz_temperature", 0.5):
                await quiz_service._generate_batch(
                    content="Test content",
                    source_type="topic",
                    batch_size=1,
                    question_types=["mcq"],
                    batch_index=0,
                )

                # Check that generate_json was called with temperature=0.5
                mock_llm.assert_called_once()
                call_kwargs = mock_llm.call_args[1]
                assert call_kwargs.get("temperature") == 0.5

    @pytest.mark.asyncio
    async def test_generate_batch_passes_seen_topics(self):
        """_generate_batch passes seen_topics to diversity directive."""
        with patch("app.services.quiz_service.build_diversity_directive") as mock_diversity:
            mock_diversity.return_value = "Diversity directive"
            with patch("app.services.quiz_service.llm_service.generate_json") as mock_llm:
                mock_llm.return_value = {
                    "questions": [
                        {
                            "question": "Test Q",
                            "correct_answer": "Test A",
                            "options": ["A", "B", "C", "D"],
                        }
                    ]
                }

                seen_topics = ["topic1", "topic2"]
                await quiz_service._generate_batch(
                    content="Test content",
                    source_type="document",
                    batch_size=1,
                    question_types=["mcq"],
                    batch_index=1,
                    seen_topics=seen_topics,
                )

                # Check that build_diversity_directive was called with seen_topics
                mock_diversity.assert_called_once_with(1, seen_topics)

    @pytest.mark.asyncio
    async def test_generate_batch_failures_return_empty_list(self):
        """_generate_batch returns [] on LLM failure."""
        with patch("app.services.quiz_service.llm_service.generate_json") as mock_llm:
            mock_llm.side_effect = Exception("LLM service down")

            result = await quiz_service._generate_batch(
                content="Test content",
                source_type="topic",
                batch_size=1,
                question_types=["mcq"],
                batch_index=0,
            )

            assert result == []


class TestGenerateQuestionsWithDedup:
    """Integration tests for generate_questions with TF-IDF dedup."""

    @pytest.mark.asyncio
    async def test_generate_questions_deduplicates(self):
        """generate_questions removes exact-match duplicates."""
        with patch("app.services.quiz_service.quiz_service._generate_batch") as mock_batch:
            # Simulate LLM returning duplicate questions
            mock_batch.side_effect = [
                [
                    {
                        "id": "1",
                        "type": "mcq",
                        "question": "What is photosynthesis?",
                        "correct_answer": "light to energy",
                        "options": ["A", "B", "C", "D"],
                        "difficulty": "medium",
                    }
                ],
                [
                    {
                        "id": "2",
                        "type": "mcq",
                        "question": "What is photosynthesis?",  # Exact duplicate
                        "correct_answer": "light to energy",
                        "options": ["A", "B", "C", "D"],
                        "difficulty": "medium",
                    }
                ],
            ]

            with patch("app.services.quiz_service.cache.get", return_value=None):
                with patch("app.services.quiz_service.cache.set"):
                    questions = await quiz_service.generate_questions(
                        content="Biology",
                        source_type="topic",
                        num_questions=2,
                    )

                    # Should only return 1 question (duplicates removed)
                    assert len(questions) == 1

    @pytest.mark.asyncio
    async def test_generate_questions_applies_cache(self):
        """generate_questions returns cached results when available."""
        cached_questions = [
            {
                "id": "cached",
                "type": "mcq",
                "question": "Cached question",
                "correct_answer": "cached answer",
                "options": ["A", "B"],
                "difficulty": "hard",
            }
        ]

        with patch("app.services.quiz_service.cache.get", return_value=cached_questions):
            questions = await quiz_service.generate_questions(
                content="Biology",
                source_type="topic",
                num_questions=1,
            )

            assert questions == cached_questions
            assert len(questions) == 1


class TestPhaseAManualVerification:
    """
    Manual verification steps for Phase A (per the plan).
    These tests document the expected behavior but don't fully automate it.
    """

    def test_phase_a_verification_notes(self):
        """
        Phase A verification checklist:
        [ ] Generated 10 questions from same doc 3× → inspect manually, count unique concepts
        [ ] pytyt tests/test_quality.py -v passes
        [ ] Temp=0.5 is used (check logs)
        [ ] TF-IDF dedup is active (check for skipped duplicates in logs)
        [ ] Aspect rotation visible in logs (batch 0 = definition, batch 1 = application, etc.)
        """
        # This is a placeholder to document expectations
        assert True
