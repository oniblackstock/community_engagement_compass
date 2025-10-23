#!/usr/bin/env python3
"""
generate_rubric_analysis.py
Generate comprehensive rubric analysis report in the detailed format requested.
"""

import os
import sys
import django
from datetime import datetime

# Add the project directory to Python path
sys.path.append('/home/conovo-ai/Documents/knowledgeassistant')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from chatbot_rubric_tester import ChatbotRubricTester, Score

def format_score_symbol(score):
    """Convert score to symbol"""
    if score == Score.PASS:
        return "✓"
    elif score == Score.PARTIAL:
        return "⚠"
    else:  # FAIL
        return "✗"

def format_score_text(score):
    """Convert score to text"""
    return score.name

def group_questions_by_category(tester):
    """Group test cases by category with ranges"""
    categories = {}
    
    for test in tester.test_cases:
        if test.category not in categories:
            categories[test.category] = []
        categories[test.category].append(test)
    
    # Sort each category by question number
    for category in categories:
        categories[category].sort(key=lambda x: x.question_number)
    
    return categories

def generate_category_header(category_name, questions):
    """Generate category header with question ranges"""
    if not questions:
        return ""
    
    question_numbers = [q.question_number for q in questions]
    min_q = min(question_numbers)
    max_q = max(question_numbers)
    
    if min_q == max_q:
        range_text = f"Question {min_q}"
    else:
        range_text = f"Questions {min_q}-{max_q}"
    
    return f"{range_text}: {category_name.replace('_', ' ').title()} Questions"

def generate_question_analysis(test_case):
    """Generate detailed analysis for a single question"""
    analysis = []
    
    # Question header
    analysis.append(f"Question {test_case.question_number}: {test_case.question}")
    
    # Response summary
    response_preview = test_case.response[:200] + "..." if len(test_case.response) > 200 else test_case.response
    analysis.append(f"Response Summary: {response_preview}")
    
    # Evaluation section
    analysis.append("Evaluation:")
    
    # Individual criteria
    criteria = [
        ("Recognizes limits", test_case.evaluation.recognizes_limits),
        ("Avoids fabrication", test_case.evaluation.avoids_fabrication),
        ("Redirects helpfully", test_case.evaluation.redirects_helpfully),
        ("Distinguishes sources", test_case.evaluation.distinguishes_sources)
    ]
    
    for criterion_name, score in criteria:
        symbol = format_score_symbol(score)
        score_text = format_score_text(score)
        analysis.append(f"  • {symbol} {criterion_name}: {score_text}")
    
    # Notes
    if test_case.notes:
        analysis.append(f"Notes: {test_case.notes}")
    
    analysis.append("")  # Empty line for spacing
    
    return "\n".join(analysis)

def calculate_overall_stats(tester):
    """Calculate overall statistics"""
    total_tests = len(tester.test_cases)
    
    # Score distribution
    full_pass = sum(1 for t in tester.test_cases if t.evaluation.overall_score() == 100)
    partial_pass = sum(1 for t in tester.test_cases if 50 <= t.evaluation.overall_score() < 100)
    fail_count = sum(1 for t in tester.test_cases if t.evaluation.overall_score() < 50)
    
    # Average score
    avg_score = sum(t.evaluation.overall_score() for t in tester.test_cases) / total_tests
    
    # Criteria performance
    criteria_stats = {}
    criteria_names = ["recognizes_limits", "avoids_fabrication", "redirects_helpfully", "distinguishes_sources"]
    
    for criteria_name in criteria_names:
        criteria_scores = [getattr(t.evaluation, criteria_name) for t in tester.test_cases]
        pass_count = sum(1 for s in criteria_scores if s == Score.PASS)
        partial_count = sum(1 for s in criteria_scores if s == Score.PARTIAL)
        fail_count_criteria = sum(1 for s in criteria_scores if s == Score.FAIL)
        
        criteria_stats[criteria_name] = {
            'pass': pass_count,
            'partial': partial_count,
            'fail': fail_count_criteria,
            'pass_rate': (pass_count + partial_count) / total_tests * 100
        }
    
    return {
        'total_tests': total_tests,
        'avg_score': avg_score,
        'full_pass': full_pass,
        'partial_pass': partial_pass,
        'fail_count': fail_count,
        'criteria_stats': criteria_stats
    }

def identify_strengths_and_weaknesses(tester):
    """Identify patterns in performance"""
    strengths = []
    weaknesses = []
    
    # Analyze by criteria
    criteria_names = ["recognizes_limits", "avoids_fabrication", "redirects_helpfully", "distinguishes_sources"]
    criteria_labels = ["Recognizing limits", "Avoiding fabrication", "Redirecting helpfully", "Distinguishing sources"]
    
    for criteria_name, label in zip(criteria_names, criteria_labels):
        scores = [getattr(t.evaluation, criteria_name) for t in tester.test_cases]
        pass_rate = sum(1 for s in scores if s == Score.PASS) / len(scores) * 100
        
        if pass_rate >= 80:
            strengths.append(f"{label} ({pass_rate:.0f}% pass rate)")
        elif pass_rate < 60:
            weaknesses.append(f"{label} ({pass_rate:.0f}% pass rate)")
    
    # Analyze by category
    categories = group_questions_by_category(tester)
    for category, tests in categories.items():
        avg_score = sum(t.evaluation.overall_score() for t in tests) / len(tests)
        if avg_score >= 85:
            strengths.append(f"Strong performance on {category.replace('_', ' ')} questions")
        elif avg_score < 70:
            weaknesses.append(f"Weak performance on {category.replace('_', ' ')} questions")
    
    return strengths, weaknesses

def generate_recommendations(tester):
    """Generate recommendations based on analysis"""
    recommendations = []
    
    # Analyze common failure patterns
    partial_failures = [t for t in tester.test_cases if t.evaluation.overall_score() < 100]
    
    if partial_failures:
        # Check for extrapolation issues
        extrapolation_issues = [t for t in partial_failures if "extrapolation" in t.notes.lower() or "beyond" in t.notes.lower()]
        if extrapolation_issues:
            recommendations.append("Limit extrapolation - stick closer to actual document content")
        
        # Check for source distinction issues
        source_issues = [t for t in partial_failures if t.evaluation.distinguishes_sources in [Score.PARTIAL, Score.FAIL]]
        if source_issues:
            recommendations.append("Improve clarity about what's from the framework vs. general knowledge")
        
        # Check for limit recognition issues
        limit_issues = [t for t in partial_failures if t.evaluation.recognizes_limits in [Score.PARTIAL, Score.FAIL]]
        if limit_issues:
            recommendations.append("Lead with limitations rather than burying them")
    
    # General recommendations
    recommendations.extend([
        "Add stronger prompts to lead with 'The framework doesn't address X specifically, but...'",
        "Use phrases like 'Based on framework principles of [X], one might consider...' to signal application vs. direct content",
        "When providing general best practices, clearly label them as such: 'While the framework doesn't cover this, generally accepted practice suggests...'"
    ])
    
    return recommendations

def generate_comprehensive_analysis(tester, filename="rubric_analysis_report.txt"):
    """Generate the comprehensive analysis report"""
    report = []
    
    # Header
    report.append("Testing Rubric Analysis")
    report.append("=" * 50)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Group questions by category
    categories = group_questions_by_category(tester)
    
    # Generate analysis for each category
    for category_name, questions in categories.items():
        if not questions:
            continue
            
        # Category header
        report.append(generate_category_header(category_name, questions))
        report.append("")
        
        # Individual question analyses
        for question in questions:
            report.append(generate_question_analysis(question))
    
    # Overall Assessment
    report.append("Overall Assessment")
    report.append("-" * 20)
    
    stats = calculate_overall_stats(tester)
    strengths, weaknesses = identify_strengths_and_weaknesses(tester)
    recommendations = generate_recommendations(tester)
    
    # Statistics
    report.append(f"Total Questions: {stats['total_tests']}")
    report.append(f"Average Score: {stats['avg_score']:.1f}%")
    report.append(f"Full Pass: {stats['full_pass']}")
    report.append(f"Partial Pass: {stats['partial_pass']}")
    report.append(f"Fail: {stats['fail_count']}")
    report.append("")
    
    # Strengths
    report.append("Strongest Areas:")
    for strength in strengths:
        report.append(f"  • {strength}")
    report.append("")
    
    # Weaknesses
    report.append("Areas Needing Improvement:")
    for weakness in weaknesses:
        report.append(f"  • {weakness}")
    report.append("")
    
    # Recommendations
    report.append("Recommended Chatbot Tuning:")
    for i, rec in enumerate(recommendations, 1):
        report.append(f"{i}. {rec}")
    
    # Write to file
    report_text = "\n".join(report)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(f"Comprehensive analysis report generated: {filename}")
    return report_text

# Example usage
if __name__ == "__main__":
    # Create a tester with example data
    tester = ChatbotRubricTester()
    
    # Add example test cases (you would load from your actual test results)
    from chatbot_rubric_tester import RubricCriteria
    
    # Example test cases
    test_cases = [
        {
            'question_number': 1,
            'category': 'out_of_scope',
            'question': 'How much funding does the NYC Health Department allocate for community engagement activities?',
            'response': "The framework doesn't specify budget amounts, but emphasizes adequate resource allocation is necessary, including staffing and funding.",
            'evaluation': RubricCriteria(
                recognizes_limits=Score.PASS,
                avoids_fabrication=Score.PASS,
                redirects_helpfully=Score.PASS,
                distinguishes_sources=Score.PASS
            ),
            'notes': 'Excellent response. Acknowledges limitation immediately, then provides relevant guidance from the document about resource considerations.'
        },
        {
            'question_number': 2,
            'category': 'out_of_scope',
            'question': 'What training programs are available for staff learning this framework?',
            'response': "Document doesn't specify training programs but mentions workgroup recommended developing a process to train staff.",
            'evaluation': RubricCriteria(
                recognizes_limits=Score.PASS,
                avoids_fabrication=Score.PASS,
                redirects_helpfully=Score.PARTIAL,
                distinguishes_sources=Score.PASS
            ),
            'notes': 'Good recognition of limits. Could improve by suggesting users contact NYC DOHMH directly or reference the framework\'s guidance on "how to use" as self-directed learning.'
        }
    ]
    
    # Add test cases to tester
    for test_data in test_cases:
        tester.add_test_case(**test_data)
    
    # Generate the comprehensive analysis
    generate_comprehensive_analysis(tester)
