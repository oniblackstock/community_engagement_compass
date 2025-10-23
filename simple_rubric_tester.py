#!/usr/bin/env python3
"""
Simple Rubric Testing Framework
Tests chatbot responses against rubric criteria using mock responses
"""

import os
import sys
import django
import logging
from datetime import datetime
from typing import Dict, List
import json

# Setup Django
sys.path.append('/home/conovo-ai/Documents/knowledgeassistant')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from chat.rubric_validator import ResponseValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleRubricTester:
    """Simple testing framework that uses mock responses"""
    
    def __init__(self):
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
    
    def get_mock_responses(self) -> Dict[str, str]:
        """Get mock responses that represent typical chatbot behavior"""
        return {
            "1": """The framework doesn't specify exact funding amounts for community engagement activities. However, it emphasizes that adequate resource allocation is necessary for effective community engagement, including staffing and funding considerations. The framework discusses the importance of having sufficient resources to support meaningful community partnerships.""",
            
            "2": """The framework doesn't specify particular training programs that are currently available. It mentions that the Community Engagement Workgroup made recommendations for "a process to train staff in the use of the framework and indicators," but doesn't detail what training was ultimately implemented. For information about current training opportunities, you could contact NYC DOHMH directly.""",
            
            "3": """The framework doesn't provide specific documented examples of completed community engagement projects. However, it discusses illustrative scenarios like infectious disease outbreak response and opioid crisis response to demonstrate how the framework principles could be applied in practice.""",
            
            "4": """According to the framework document published in May 2017, Dr. Mary T. Bassett was the Commissioner of Health at that time. However, I cannot confirm who the current Commissioner is, as that information would be outside the framework. You can find current leadership information at nyc.gov/health.""",
            
            "5": """The framework doesn't provide a detailed comparison to the CDC's community engagement model. It mentions that the framework was adapted from CDC's work, but doesn't elaborate on specific similarities or differences between the two approaches.""",
            
            "6": """The framework was published in May 2017, but the document doesn't contain information about subsequent activities of the Community Engagement Workgroup. For current information about ongoing workgroup activities, you would need to contact NYC DOHMH directly.""",
            
            "7": """The framework doesn't list specific community advisory boards that are currently active. It discusses advisory boards as one consultation technique that can be used, emphasizing their importance for gathering community input, but doesn't specify which boards are currently operating.""",
            
            "8": """The framework doesn't compare NYC's approach to other health departments. It focuses specifically on NYC DOHMH's community engagement framework and doesn't provide information about how other departments approach community engagement differently.""",
            
            "9": """The framework doesn't provide specific guidance on community engagement during pandemics like COVID-19, as it was published in 2017 before the pandemic. However, it emphasizes core principles that would be relevant: transparency, building trust through consistent engagement, and understanding community culture and previous experiences.""",
            
            "10": """The framework doesn't specifically address engaging immigrant communities who fear government agencies. However, it emphasizes principles of transparency, trust-building, and understanding community culture that would be relevant. The framework discusses the importance of acknowledging historical experiences and building relationships based on mutual respect.""",
            
            "11": """The framework doesn't provide specific cultural considerations for Asian American communities in NYC. It emphasizes the importance of understanding community culture, norms, and previous experiences with outside groups, but doesn't offer detailed guidance for specific cultural groups.""",
            
            "12": """The framework doesn't use "ROI" (Return on Investment) terminology specifically. However, it discusses evaluation and assessment of community engagement efforts, emphasizing the importance of measuring outcomes and impact to ensure accountability and continuous improvement.""",
            
            "13": """The framework doesn't recommend specific software tools for tracking community engagement efforts. It discusses the importance of documentation and tracking engagement activities, but doesn't specify particular technology solutions or platforms.""",
            
            "14": """The framework doesn't use the term "social determinants of health" specifically, but it emphasizes that advancing health equity requires identifying "the underlying social and systemic injustices that drive health inequities" and designing strategies to change these systems.""",
            
            "15": """The framework was designed specifically for NYC DOHMH, but it discusses adaptability considerations. It emphasizes that community engagement approaches should be tailored to local context, community needs, and organizational capacity, suggesting that adaptation to other health departments would require careful consideration of local factors.""",
            
            "16": """The framework doesn't address environmental justice organizing specifically, as it was designed for public health community engagement. However, the core principles of transparency, accountability, and community-centered approaches could potentially inform environmental justice work, though this would be an application beyond the framework's intended scope.""",
            
            "17": """The framework doesn't provide specific examples of shared leadership in housing advocacy campaigns. It describes shared leadership as a collaboration technique where decision-making authority is distributed among partners, but doesn't offer detailed scenarios for specific policy areas like housing.""",
            
            "18": """The framework was designed for government agencies, specifically NYC DOHMH, but it discusses principles that could be relevant to nonprofits. However, nonprofits would need to adapt the framework to their organizational structure, resources, and community context, as the framework assumes certain government capacities and authorities.""",
            
            "19": """The framework doesn't provide specific strategies for advocating for more resources with supervisors. However, it emphasizes the importance of adequate resource allocation for effective community engagement and discusses how to make the case for community engagement based on its value for advancing health equity.""",
            
            "20": """The framework doesn't identify one engagement type as "most effective." It emphasizes that the choice of engagement approach should depend on the specific context, community needs, and desired outcomes. The framework presents different engagement types as tools to be selected based on appropriateness for the situation.""",
            
            "21": """The framework doesn't specify minimum budget amounts needed for meaningful collaboration. It emphasizes that adequate resource allocation is necessary for effective community engagement, but doesn't provide specific dollar amounts or budget recommendations.""",
            
            "22": """The framework doesn't provide specific timeframes for moving from consultation to collaboration. It describes consultation and collaboration as different approaches that can be used based on context and goals, but doesn't specify how long transitions between approaches should take.""",
            
            "23": """The framework doesn't directly address when it might be appropriate to skip community engagement. However, it emphasizes that community engagement is essential for advancing health equity and addressing systemic injustices, suggesting that engagement should be the default approach rather than an optional activity.""",
            
            "24": """The framework doesn't provide specific protocols for addressing disagreement with community members. However, it emphasizes principles of transparency, accountability, and mutual respect that would be relevant for navigating conflicts and maintaining productive community relationships."""
        }
    
    def test_single_question(self, question_data: Dict, mock_response: str) -> Dict:
        """Test a single question with mock response"""
        question_id = question_data["id"]
        question_text = question_data["question"]
        category = question_data["category"]
        expected_behavior = question_data["expected_behavior"]
        
        logger.info(f"Testing Question {question_id}: {question_text[:50]}...")
        
        try:
            # Get rubric scores
            rubric_scores = ResponseValidator.get_rubric_score(question_text, mock_response)
            
            # Get detailed validation
            validation_result = ResponseValidator.validate(question_text, mock_response)
            
            # Calculate word count
            word_count = len(mock_response.split())
            
            # Determine if response meets expected behavior
            meets_expectations = self._evaluate_expected_behavior(
                question_text, mock_response, expected_behavior, rubric_scores
            )
            
            result = {
                "question_id": question_id,
                "question": question_text,
                "category": category,
                "expected_behavior": expected_behavior,
                "response": mock_response,
                "word_count": word_count,
                "is_valid": validation_result["is_valid"],
                "warnings": validation_result["warnings"],
                "rubric_scores": rubric_scores,
                "meets_expectations": meets_expectations,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Question {question_id} completed - Score: {rubric_scores['overall_score']:.1f}%")
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
        mock_responses = self.get_mock_responses()
        results = []
        
        for question_data in questions:
            question_id = str(question_data["id"])
            mock_response = mock_responses.get(question_id, "No mock response available")
            
            result = self.test_single_question(question_data, mock_response)
            results.append(result)
        
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
            filename = f"simple_rubric_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.info(f"Results saved to {filename}")
        return filename

def main():
    """Main function to run comprehensive testing"""
    print("Starting Simple Rubric Testing...")
    print("=" * 50)
    
    tester = SimpleRubricTester()
    
    # Run tests
    results = tester.run_comprehensive_test()
    
    # Generate report
    report = tester.generate_detailed_report()
    
    # Save results
    results_file = tester.save_results()
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"simple_rubric_report_{timestamp}.md"
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
