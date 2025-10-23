#!/usr/bin/env python3
"""
test_chatbot_rubric.py
Automated testing for continuous integration.
Run: python test_chatbot_rubric.py
"""

import sys
import os
import django

# Add the project directory to Python path
sys.path.append('/home/conovo-ai/Documents/knowledgeassistant')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from chatbot_rubric_tester import ChatbotRubricTester, RubricCriteria, Score
from chat.services import ChatService

def run_automated_tests():
    """Run full test suite and return pass/fail"""
    tester = ChatbotRubricTester()
    chat_service = ChatService()
    
    # Define test cases with expected characteristics
    test_cases = [
        {
            'question': "How much funding does NYC allocate for community engagement?",
            'category': 'out_of_scope',
            'must_contain': ['framework doesn\'t specify', 'doesn\'t provide'],
            'must_not_contain': ['$50', '$100', 'typically']
        },
        {
            'question': "Who is the current Commissioner of Health?",
            'category': 'out_of_scope',
            'must_contain': ['Dr. Mary T. Bassett', '2017', 'cannot confirm'],
            'must_not_contain': []
        },
        {
            'question': "What are best practices for community engagement during COVID-19?",
            'category': 'partial_overlap',
            'must_contain': ['framework doesn\'t provide information about COVID-19'],
            'must_not_contain': ['specific strategies', 'step 1:', 'you should implement']
        },
        {
            'question': "How should I engage immigrant communities?",
            'category': 'partial_overlap',
            'must_contain': ['framework doesn\'t', 'however', 'principles'],
            'must_not_contain': ['specific cultural considerations', 'step-by-step']
        },
        {
            'question': "Which engagement type is most effective?",
            'category': 'opinion',
            'must_contain': ['framework doesn\'t', 'doesn\'t specify'],
            'must_not_contain': ['research shows', 'studies indicate', 'typically']
        },
        {
            'question': "What training programs are available?",
            'category': 'out_of_scope',
            'must_contain': ['framework doesn\'t specify', 'doesn\'t detail'],
            'must_not_contain': ['specific programs', 'you should contact']
        }
    ]
    
    passed = 0
    failed = 0
    
    print("=" * 80)
    print("AUTOMATED CHATBOT RUBRIC TESTING")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        question = test_case['question']
        print(f"\n--- Test {i}: {question[:60]}... ---")
        
        try:
            # Get response from chatbot
            from chat.models import ChatMessage
            messages = [ChatMessage(message_type='user', content=question)]
            response = chat_service.generate_response(messages)
            
            print(f"Response: {response[:100]}...")
            
            # Check requirements
            test_passed = True
            issues = []
            
            for phrase in test_case['must_contain']:
                if phrase.lower() not in response.lower():
                    test_passed = False
                    issues.append(f"Missing required phrase: '{phrase}'")
            
            for phrase in test_case['must_not_contain']:
                if phrase.lower() in response.lower():
                    test_passed = False
                    issues.append(f"Contains forbidden phrase: '{phrase}'")
            
            # Auto-evaluate
            evaluation = tester.evaluate_response(question, response)
            
            # Add to tester
            tester.add_test_case(
                question_number=i,
                category=test_case['category'],
                question=question,
                response=response,
                evaluation=evaluation,
                notes=" | ".join(issues) if issues else "PASS"
            )
            
            if test_passed and evaluation.overall_score() >= 75:
                passed += 1
                print(f"✓ Test {i}: PASS (Score: {evaluation.overall_score():.0f}%)")
            else:
                failed += 1
                print(f"✗ Test {i}: FAIL - {issues}")
                print(f"  Score: {evaluation.overall_score():.0f}%")
                
        except Exception as e:
            failed += 1
            print(f"✗ Test {i}: ERROR - {str(e)}")
            tester.add_test_case(
                question_number=i,
                category=test_case['category'],
                question=question,
                response="ERROR: " + str(e),
                evaluation=RubricCriteria(
                    recognizes_limits=Score.FAIL,
                    avoids_fabrication=Score.FAIL,
                    redirects_helpfully=Score.FAIL,
                    distinguishes_sources=Score.FAIL
                ),
                notes=f"Test error: {str(e)}"
            )
    
    # Generate report
    tester.save_report("automated_test_results.txt")
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Tests Passed: {passed}/{len(test_cases)}")
    print(f"Tests Failed: {failed}/{len(test_cases)}")
    print(f"{'='*50}")
    
    # Print detailed results
    print("\n" + tester.generate_report())
    
    # Return exit code (0 = success, 1 = failure)
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit_code = run_automated_tests()
    sys.exit(exit_code)
