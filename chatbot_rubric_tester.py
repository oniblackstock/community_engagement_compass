#!/usr/bin/env python3
"""
chatbot_rubric_tester.py
Simple script to test chatbot responses against the rubric criteria.
Run this manually to evaluate responses.
"""

from dataclasses import dataclass
from typing import List, Dict
from enum import Enum

class Score(Enum):
    PASS = "✓ PASS"
    PARTIAL = "⚠ PARTIAL"
    FAIL = "✗ FAIL"

@dataclass
class RubricCriteria:
    """Four criteria for evaluating responses"""
    recognizes_limits: Score
    avoids_fabrication: Score
    redirects_helpfully: Score
    distinguishes_sources: Score

    def overall_score(self) -> float:
        """Calculate percentage score (0-100)"""
        scores = [
            self.recognizes_limits,
            self.avoids_fabrication,
            self.redirects_helpfully,
            self.distinguishes_sources
        ]
        pass_count = sum(1 for s in scores if s == Score.PASS)
        partial_count = sum(1 for s in scores if s == Score.PARTIAL)
        return ((pass_count * 1.0) + (partial_count * 0.5)) / 4 * 100

@dataclass
class TestCase:
    """Individual test question and response"""
    question_number: int
    category: str  # "out_of_scope", "partial_overlap", "application", "opinion"
    question: str
    response: str
    evaluation: RubricCriteria
    notes: str

class ChatbotRubricTester:
    def __init__(self):
        self.test_cases: List[TestCase] = []

    def add_test_case(self, question_number: int, category: str, question: str,
                     response: str, evaluation: RubricCriteria, notes: str = ""):
        """Add a test case"""
        test_case = TestCase(
            question_number=question_number,
            category=category,
            question=question,
            response=response,
            evaluation=evaluation,
            notes=notes
        )
        self.test_cases.append(test_case)

    def evaluate_response(self, question: str, response: str) -> RubricCriteria:
        """
        Semi-automated evaluation with helper checks.
        Returns suggested scores that reviewer can confirm.
        """
        # Initialize with PASS, then downgrade based on checks
        recognizes = Score.PASS
        fabrication = Score.PASS
        redirects = Score.PASS
        distinguishes = Score.PASS
        
        response_lower = response.lower()
        question_lower = question.lower()

        # Check 1: Recognizes limits
        out_of_scope_indicators = ['current', 'latest', 'specific', 'how much', 'who is',
                                  'what happened after', 'other departments', 'covid']
        limitation_phrases = ["framework doesn't", "document doesn't", "doesn't provide",
                            "doesn't specify", "doesn't address", "doesn't cover",
                            "not in the framework", "not addressed"]
        
        if any(indicator in question_lower for indicator in out_of_scope_indicators):
            if not any(phrase in response_lower for phrase in limitation_phrases):
                recognizes = Score.FAIL
            elif response.index(next(p for p in limitation_phrases if p in response_lower)) > 200:
                recognizes = Score.PARTIAL  # Buried limitation

        # Check 2: Avoids fabrication
        fabrication_indicators = [
            ('$', ['framework doesn\'t specify', 'doesn\'t provide']),  # Money without disclaimer
            ('typically requires', []),
            ('best practice is to', ['framework']),
            ('you should', ['framework recommends', 'framework emphasizes']),
            ('step 1:', []),  # Detailed steps not in doc
            ('for example, you could', ['framework']),
        ]
        
        for indicator, required_disclaimers in fabrication_indicators:
            if indicator in response_lower:
                if required_disclaimers:
                    if not any(disclaimer in response_lower for disclaimer in required_disclaimers):
                        fabrication = Score.PARTIAL
                else:
                    fabrication = Score.PARTIAL

        # Check 3: Redirects helpfully
        if any(phrase in response_lower for phrase in limitation_phrases):
            # Has limitation, check for helpful redirect
            helpful_phrases = ['however', 'it does discuss', 'the framework emphasizes',
                             'you might', 'you could check', 'relevant principles']
            if not any(phrase in response_lower for phrase in helpful_phrases):
                redirects = Score.PARTIAL

        # Check 4: Distinguishes sources
        blending_indicators = [
            'generally', 'typically', 'usually', 'often', 'common practice',
            'best practices include', 'research shows', 'studies indicate'
        ]
        framework_attribution = ['the framework', 'the document', 'according to']
        
        has_general = any(indicator in response_lower for indicator in blending_indicators)
        has_attribution = any(attr in response_lower for attr in framework_attribution)
        
        if has_general and not has_attribution:
            distinguishes = Score.PARTIAL

        return RubricCriteria(
            recognizes_limits=recognizes,
            avoids_fabrication=fabrication,
            redirects_helpfully=redirects,
            distinguishes_sources=distinguishes
        )

    def generate_report(self) -> str:
        """Generate text report of all test results"""
        report = ["=" * 80]
        report.append("CHATBOT TESTING RUBRIC REPORT")
        report.append("=" * 80)
        report.append("")

        # Summary by category
        categories = {}
        for test in self.test_cases:
            if test.category not in categories:
                categories[test.category] = []
            categories[test.category].append(test)

        for category, tests in categories.items():
            report.append(f"\n## {category.upper().replace('_', ' ')}")
            report.append("-" * 80)
            for test in tests:
                report.append(f"\n### Question {test.question_number}: {test.question[:80]}...")
                report.append(f"**Evaluation:**")
                report.append(f" - Recognizes limits: {test.evaluation.recognizes_limits.value}")
                report.append(f" - Avoids fabrication: {test.evaluation.avoids_fabrication.value}")
                report.append(f" - Redirects helpfully: {test.evaluation.redirects_helpfully.value}")
                report.append(f" - Distinguishes sources: {test.evaluation.distinguishes_sources.value}")
                report.append(f" - **Overall Score: {test.evaluation.overall_score():.0f}%**")
                if test.notes:
                    report.append(f"**Notes:** {test.notes}")
                report.append("")

        # Overall statistics
        report.append("\n" + "=" * 80)
        report.append("OVERALL STATISTICS")
        report.append("=" * 80)
        total_tests = len(self.test_cases)
        avg_score = sum(t.evaluation.overall_score() for t in self.test_cases) / total_tests
        report.append(f"Total Tests: {total_tests}")
        report.append(f"Average Score: {avg_score:.1f}%")

        # Count by score level
        full_pass = sum(1 for t in self.test_cases if t.evaluation.overall_score() == 100)
        partial = sum(1 for t in self.test_cases if 50 <= t.evaluation.overall_score() < 100)
        failing = sum(1 for t in self.test_cases if t.evaluation.overall_score() < 50)
        
        report.append(f"\nFull Pass (100%): {full_pass}")
        report.append(f"Partial Pass (50-99%): {partial}")
        report.append(f"Failing (<50%): {failing}")

        # Category breakdown
        report.append("\n## Performance by Category:")
        for category, tests in categories.items():
            cat_avg = sum(t.evaluation.overall_score() for t in tests) / len(tests)
            report.append(f" - {category}: {cat_avg:.1f}%")

        return "\n".join(report)

    def save_report(self, filename: str = "rubric_report.txt"):
        """Save report to file"""
        report = self.generate_report()
        with open(filename, 'w') as f:
            f.write(report)
        print(f"Report saved to {filename}")


# Example usage
if __name__ == "__main__":
    tester = ChatbotRubricTester()
    
    # Example: Add test case manually
    tester.add_test_case(
        question_number=1,
        category="out_of_scope",
        question="How much funding does the NYC Health Department allocate for community engagement activities?",
        response="The Health Department doesn't allocate a specific amount...",  # Paste actual response
        evaluation=RubricCriteria(
            recognizes_limits=Score.PASS,
            avoids_fabrication=Score.PASS,
            redirects_helpfully=Score.PASS,
            distinguishes_sources=Score.PASS
        ),
        notes="Excellent response. Acknowledges limitation immediately."
    )
    
    # Or use semi-automated evaluation
    question = "How much funding does NYC allocate?"
    response = "The framework doesn't specify amounts, but emphasizes adequate resources..."
    evaluation = tester.evaluate_response(question, response)
    tester.add_test_case(
        question_number=1,
        category="out_of_scope",
        question=question,
        response=response,
        evaluation=evaluation,
        notes="Auto-evaluated, needs manual review"
    )
    
    # Generate and save report
    print(tester.generate_report())
    tester.save_report()
