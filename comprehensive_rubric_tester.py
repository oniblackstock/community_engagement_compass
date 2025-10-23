#!/usr/bin/env python3
"""
Comprehensive Rubric Testing Framework
Tests chatbot responses against rubric criteria using actual services.py prompts
"""

import os
import sys
import django
import logging
from datetime import datetime
from typing import Dict, List, Tuple
import json

# Setup CUDA environment BEFORE importing torch
os.environ['CUDA_VISIBLE_DEVICES'] = '0'  # Use first GPU
os.environ['TORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'

# Setup Django
sys.path.append('/home/conovo-ai/Documents/knowledgeassistant')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from chat.services import ChatService, validate_chatbot_response_with_rubric
from chat.rubric_validator import ResponseValidator
from chat.models import ChatMessage, ChatSession
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

User = get_user_model()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveRubricTester:
    """Comprehensive testing framework for chatbot responses"""
    
    def __init__(self):
        # Verify CUDA is working
        import torch
        if torch.cuda.is_available():
            print(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
            print(f"✓ CUDA device count: {torch.cuda.device_count()}")
        else:
            print("⚠ CUDA not available, using CPU")
        
        self.chat_service = ChatService()
        self.test_results = []
        
    def get_test_questions(self) -> List[Dict]:
        """Get comprehensive test questions organized by category"""
        return [
            # Questions 1-8: Out of Scope Questions
            {
                "id": 1,
                "question": "How much funding does the NYC Health Department allocate for community engagement activities?",
                "category": "Out of Scope",
                "expected_behavior": "Should acknowledge framework doesn't specify amounts"
            },
            {
                "id": 2,
                "question": "What training programs are available for staff learning this framework?",
                "category": "Out of Scope",
                "expected_behavior": "Should acknowledge framework doesn't specify training programs"
            },
            {
                "id": 3,
                "question": "Can you give me examples of successful community engagement projects the Health Department has done?",
                "category": "Out of Scope",
                "expected_behavior": "Should acknowledge framework doesn't provide specific examples"
            },
            {
                "id": 4,
                "question": "Who is the current Commissioner of Health in NYC?",
                "category": "Out of Scope",
                "expected_behavior": "Should acknowledge temporal limitations of framework"
            },
            {
                "id": 5,
                "question": "How does this framework compare to the CDC's community engagement model?",
                "category": "Out of Scope",
                "expected_behavior": "Should acknowledge framework doesn't provide detailed comparison"
            },
            {
                "id": 6,
                "question": "What happened with the Community Engagement Workgroup after 2017?",
                "category": "Out of Scope",
                "expected_behavior": "Should acknowledge temporal limitations"
            },
            {
                "id": 7,
                "question": "Are there any community advisory boards currently active at the Health Department?",
                "category": "Out of Scope",
                "expected_behavior": "Should acknowledge framework doesn't specify current boards"
            },
            {
                "id": 8,
                "question": "How do other health departments approach community engagement differently?",
                "category": "Out of Scope",
                "expected_behavior": "Should acknowledge framework doesn't compare to other departments"
            },
            
            # Questions 9-14: Partial Overlap Questions
            {
                "id": 9,
                "question": "What are best practices for community engagement during the COVID-19 pandemic?",
                "category": "Partial Overlap",
                "expected_behavior": "Should acknowledge COVID-19 predates framework, then apply principles"
            },
            {
                "id": 10,
                "question": "How should I engage immigrant communities who are afraid of government agencies?",
                "category": "Partial Overlap",
                "expected_behavior": "Should acknowledge specific scenario not addressed, then apply principles"
            },
            {
                "id": 11,
                "question": "What specific cultural considerations should I know when working with Asian American communities in NYC?",
                "category": "Partial Overlap",
                "expected_behavior": "Should acknowledge specific cultural guidance not provided"
            },
            {
                "id": 12,
                "question": "How do I measure ROI on community engagement activities?",
                "category": "Partial Overlap",
                "expected_behavior": "Should acknowledge framework doesn't use ROI terminology"
            },
            {
                "id": 13,
                "question": "What software tools can help track community engagement efforts?",
                "category": "Partial Overlap",
                "expected_behavior": "Should acknowledge framework doesn't recommend specific software"
            },
            {
                "id": 14,
                "question": "How does community engagement relate to the social determinants of health?",
                "category": "Partial Overlap",
                "expected_behavior": "Should acknowledge framework doesn't use SDOH terminology specifically"
            },
            
            # Questions 15-19: Application Beyond Document
            {
                "id": 15,
                "question": "I work for a different health department - can I adapt this framework?",
                "category": "Application Beyond Document",
                "expected_behavior": "Should acknowledge framework's specific context"
            },
            {
                "id": 16,
                "question": "How would this framework apply to environmental justice organizing?",
                "category": "Application Beyond Document",
                "expected_behavior": "Should acknowledge framework is for public health"
            },
            {
                "id": 17,
                "question": "What would shared leadership look like for a housing advocacy campaign?",
                "category": "Application Beyond Document",
                "expected_behavior": "Should acknowledge hypothetical application"
            },
            {
                "id": 18,
                "question": "Should nonprofits use this same framework?",
                "category": "Application Beyond Document",
                "expected_behavior": "Should acknowledge framework is government-specific"
            },
            {
                "id": 19,
                "question": "How do I convince my supervisor to allocate more resources to community engagement?",
                "category": "Application Beyond Document",
                "expected_behavior": "Should acknowledge framework doesn't provide persuasion strategies"
            },
            
            # Questions 20-24: Opinion/Judgment Questions
            {
                "id": 20,
                "question": "Which engagement type is most effective?",
                "category": "Opinion/Judgment",
                "expected_behavior": "Should acknowledge framework doesn't identify 'most effective'"
            },
            {
                "id": 21,
                "question": "What's the minimum budget needed for meaningful collaboration?",
                "category": "Opinion/Judgment",
                "expected_behavior": "Should acknowledge framework doesn't specify amounts"
            },
            {
                "id": 22,
                "question": "How long does it take to move from consultation to collaboration?",
                "category": "Opinion/Judgment",
                "expected_behavior": "Should acknowledge framework doesn't provide specific timeframes"
            },
            {
                "id": 23,
                "question": "Is it ever okay to skip community engagement?",
                "category": "Opinion/Judgment",
                "expected_behavior": "Should acknowledge framework doesn't address 'skipping' engagement"
            },
            {
                "id": 24,
                "question": "What should I do if community members disagree with our proposal?",
                "category": "Opinion/Judgment",
                "expected_behavior": "Should acknowledge framework doesn't provide conflict resolution protocols"
            }
        ]
    
    def test_single_question(self, question_data: Dict) -> Dict:
        """Test a single question and return detailed results"""
        question_id = question_data["id"]
        question_text = question_data["question"]
        category = question_data["category"]
        expected_behavior = question_data["expected_behavior"]
        
        logger.info(f"Testing Question {question_id}: {question_text[:50]}...")
        
        try:
            # Create a mock chat session and message
            # Get or create a test user
            test_user, created = User.objects.get_or_create(
                email='admin@gmail.com',
                defaults={'name': 'admin', 'password': make_password('prince1018')}
            )
            
            session = ChatSession.objects.create(
                user=test_user,
                session_name=f"Test Session {question_id}"
            )
            
            # Create user message
            user_message = ChatMessage.objects.create(
                session=session,
                content=question_text,
                message_type='user'
            )
            
            # Generate response using actual ChatService
            messages = [user_message]
            response_text = self.chat_service.generate_response(messages)
            
            # Validate response with rubric
            is_valid, warnings, rubric_scores = validate_chatbot_response_with_rubric(
                response_text, question_text
            )
            
            # Get detailed rubric analysis
            rubric_analysis = ResponseValidator.get_rubric_score(question_text, response_text)
            
            # Calculate word count
            word_count = len(response_text.split())
            
            # Determine if response meets expected behavior
            meets_expectations = self._evaluate_expected_behavior(
                question_text, response_text, expected_behavior, rubric_scores
            )
            
            result = {
                "question_id": question_id,
                "question": question_text,
                "category": category,
                "expected_behavior": expected_behavior,
                "response": response_text,
                "word_count": word_count,
                "is_valid": is_valid,
                "warnings": warnings,
                "rubric_scores": rubric_scores,
                "rubric_analysis": rubric_analysis,
                "meets_expectations": meets_expectations,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Question {question_id} completed - Score: {rubric_analysis['overall_score']:.1f}%")
            return result
            
        except Exception as e:
            logger.error(f"Error testing question {question_id}: {str(e)}")
            return {
                "question_id": question_id,
                "question": question_text,
                "category": category,
                "expected_behavior": expected_behavior,
                "response": f"ERROR: {str(e)}",
                "word_count": 0,
                "is_valid": False,
                "warnings": [f"Test error: {str(e)}"],
                "rubric_scores": None,
                "rubric_analysis": None,
                "meets_expectations": False,
                "timestamp": datetime.now().isoformat()
            }
    
    def _evaluate_expected_behavior(self, question: str, response: str, expected: str, rubric_scores: Dict) -> bool:
        """Evaluate if response meets expected behavior"""
        if not rubric_scores:
            return False
            
        response_lower = response.lower()
        question_lower = question.lower()
        
        # Check if response acknowledges limitations appropriately
        limitation_phrases = [
            "framework doesn't", "document doesn't", "doesn't provide",
            "doesn't specify", "doesn't address", "doesn't cover"
        ]
        
        has_limitation_acknowledgment = any(phrase in response_lower for phrase in limitation_phrases)
        
        # For out-of-scope questions, should have limitation acknowledgment
        if "out of scope" in expected.lower():
            return has_limitation_acknowledgment and rubric_scores.get('recognizes_limits') in ['PASS', 'PARTIAL']
        
        # For partial overlap, should acknowledge limitations but provide relevant guidance
        if "partial overlap" in expected.lower():
            return (has_limitation_acknowledgment and 
                   rubric_scores.get('redirects_helpfully') in ['PASS', 'PARTIAL'])
        
        # For application questions, should acknowledge framework's specific context
        if "application" in expected.lower():
            return rubric_scores.get('distinguishes_sources') in ['PASS', 'PARTIAL']
        
        # For opinion questions, should avoid making judgments not in framework
        if "opinion" in expected.lower():
            return rubric_scores.get('avoids_fabrication') in ['PASS', 'PARTIAL']
        
        return True
    
    def run_comprehensive_test(self) -> List[Dict]:
        """Run comprehensive test on all questions"""
        logger.info("Starting comprehensive rubric testing...")
        
        questions = self.get_test_questions()
        results = []
        
        for question_data in questions:
            result = self.test_single_question(question_data)
            results.append(result)
            
            # Small delay to avoid overwhelming the system
            import time
            time.sleep(0.5)
        
        self.test_results = results
        logger.info(f"Completed testing {len(results)} questions")
        return results
    
    def generate_detailed_report(self) -> str:
        """Generate detailed report in the specified format"""
        if not self.test_results:
            return "No test results available. Run tests first."
        
        report_lines = []
        report_lines.append("# Testing Rubric Analysis")
        report_lines.append("")
        
        # Group results by category
        categories = {}
        for result in self.test_results:
            category = result["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        # Generate report for each category
        for category_name, category_results in categories.items():
            report_lines.append(f"## {category_name} Questions")
            report_lines.append("")
            
            for result in category_results:
                self._add_question_analysis(report_lines, result)
                report_lines.append("")
        
        # Add overall assessment
        self._add_overall_assessment(report_lines)
        
        return "\n".join(report_lines)
    
    def _add_question_analysis(self, report_lines: List[str], result: Dict):
        """Add detailed analysis for a single question"""
        q_id = result["question_id"]
        question = result["question"]
        response = result["response"]
        rubric_scores = result.get("rubric_scores", {})
        rubric_analysis = result.get("rubric_analysis", {})
        
        report_lines.append(f"**Question {q_id}:** {question}")
        report_lines.append("")
        report_lines.append(f"**Response Summary:** {self._summarize_response(response)}")
        report_lines.append("")
        report_lines.append("**Evaluation:**")
        
        # Add rubric scores
        if rubric_scores:
            for criterion, score in rubric_scores.items():
                if criterion != 'overall_score':
                    status_symbol = "✓" if score == "PASS" else "⚠" if score == "PARTIAL" else "✗"
                    report_lines.append(f"{status_symbol} {criterion.replace('_', ' ').title()}: {score}")
        
        report_lines.append("")
        report_lines.append(f"**Notes:** {self._generate_notes(result)}")
    
    def _summarize_response(self, response: str) -> str:
        """Generate a concise summary of the response"""
        if len(response) <= 200:
            return response
        
        # Extract first sentence or first 150 characters
        sentences = response.split('. ')
        if len(sentences) > 0 and len(sentences[0]) <= 150:
            return sentences[0] + "."
        else:
            return response[:150] + "..."
    
    def _generate_notes(self, result: Dict) -> str:
        """Generate analysis notes for the response"""
        rubric_scores = result.get("rubric_scores", {})
        warnings = result.get("warnings", [])
        meets_expectations = result.get("meets_expectations", False)
        
        notes = []
        
        if meets_expectations:
            notes.append("Response meets expected behavior for this question type.")
        else:
            notes.append("Response could be improved to better meet expected behavior.")
        
        if warnings:
            notes.append(f"Warnings: {', '.join(warnings[:2])}")  # Limit to first 2 warnings
        
        # Add specific feedback based on rubric scores
        if rubric_scores:
            if rubric_scores.get('recognizes_limits') == 'FAIL':
                notes.append("Should acknowledge framework limitations more clearly.")
            elif rubric_scores.get('recognizes_limits') == 'PARTIAL':
                notes.append("Limitation acknowledgment could be improved.")
            
            if rubric_scores.get('avoids_fabrication') == 'FAIL':
                notes.append("Contains fabricated information not in framework.")
            elif rubric_scores.get('avoids_fabrication') == 'PARTIAL':
                notes.append("Some prescriptive language without attribution.")
            
            if rubric_scores.get('redirects_helpfully') == 'PARTIAL':
                notes.append("Could redirect more helpfully after acknowledging limitations.")
            
            if rubric_scores.get('distinguishes_sources') == 'PARTIAL':
                notes.append("Blends general advice with framework content.")
        
        return " ".join(notes)
    
    def _add_overall_assessment(self, report_lines: List[str]):
        """Add overall assessment section"""
        report_lines.append("## Overall Assessment")
        report_lines.append("")
        
        # Calculate statistics
        total_questions = len(self.test_results)
        valid_responses = sum(1 for r in self.test_results if r.get("is_valid", False))
        meets_expectations = sum(1 for r in self.test_results if r.get("meets_expectations", False))
        
        # Calculate average scores by criterion
        rubric_scores_by_criterion = {
            'recognizes_limits': {'PASS': 0, 'PARTIAL': 0, 'FAIL': 0},
            'avoids_fabrication': {'PASS': 0, 'PARTIAL': 0, 'FAIL': 0},
            'redirects_helpfully': {'PASS': 0, 'PARTIAL': 0, 'FAIL': 0},
            'distinguishes_sources': {'PASS': 0, 'PARTIAL': 0, 'FAIL': 0}
        }
        
        for result in self.test_results:
            rubric_scores = result.get("rubric_scores", {})
            if rubric_scores:  # Check if rubric_scores is not None
                for criterion, scores in rubric_scores_by_criterion.items():
                    if criterion in rubric_scores:
                        score = rubric_scores[criterion]
                        if score in scores:
                            scores[score] += 1
        
        report_lines.append("**Strongest Areas:**")
        strongest = []
        for criterion, scores in rubric_scores_by_criterion.items():
            pass_rate = scores['PASS'] / total_questions * 100 if total_questions > 0 else 0
            if pass_rate >= 80:
                strongest.append(f"- {criterion.replace('_', ' ').title()} ({pass_rate:.1f}% PASS)")
        
        if strongest:
            report_lines.extend(strongest)
        else:
            report_lines.append("- No areas with >80% PASS rate")
        
        report_lines.append("")
        report_lines.append("**Areas Needing Improvement:**")
        
        improvement_areas = []
        for criterion, scores in rubric_scores_by_criterion.items():
            fail_rate = scores['FAIL'] / total_questions * 100 if total_questions > 0 else 0
            partial_rate = scores['PARTIAL'] / total_questions * 100 if total_questions > 0 else 0
            
            if fail_rate > 20 or partial_rate > 40:
                improvement_areas.append(f"- {criterion.replace('_', ' ').title()} ({fail_rate:.1f}% FAIL, {partial_rate:.1f}% PARTIAL)")
        
        if improvement_areas:
            report_lines.extend(improvement_areas)
        else:
            report_lines.append("- All areas performing well")
        
        report_lines.append("")
        report_lines.append("**Recommended Chatbot Tuning:**")
        report_lines.append("- Add stronger prompts to lead with 'The framework doesn't address X specifically, but...'")
        report_lines.append("- Limit extrapolation - stick closer to actual document content")
        report_lines.append("- Use phrases like 'Based on framework principles of [X], one might consider...' to signal application vs. direct content")
        report_lines.append("- When providing general best practices, clearly label them as such: 'While the framework doesn't cover this, generally accepted practice suggests...'")
    
    def save_results(self, filename: str = None):
        """Save test results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comprehensive_rubric_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.info(f"Results saved to {filename}")
        return filename

def main():
    """Main function to run comprehensive testing"""
    print("Starting Comprehensive Rubric Testing...")
    print("=" * 50)
    
    tester = ComprehensiveRubricTester()
    
    # Run tests
    results = tester.run_comprehensive_test()
    
    # Generate report
    report = tester.generate_detailed_report()
    
    # Save results
    results_file = tester.save_results()
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"comprehensive_rubric_report_{timestamp}.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\nTesting completed!")
    print(f"Results saved to: {results_file}")
    print(f"Report saved to: {report_file}")
    print("\nReport Preview:")
    print("=" * 50)
    print(report[:1000] + "..." if len(report) > 1000 else report)

if __name__ == "__main__":
    main()
