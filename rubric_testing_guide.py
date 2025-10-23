#!/usr/bin/env python3
"""
rubric_testing_guide.py
Guide for using the chatbot rubric testing tools.
"""

import os
import sys

def print_guide():
    """Print usage guide for all rubric testing tools"""
    
    print("=" * 80)
    print("CHATBOT RUBRIC TESTING TOOLS - USAGE GUIDE")
    print("=" * 80)
    
    print("\n📋 AVAILABLE TOOLS:")
    print("-" * 40)
    
    print("\n1. 🤖 INTERACTIVE TESTING")
    print("   File: interactive_rubric_test.py")
    print("   Usage: python interactive_rubric_test.py")
    print("   Description: Interactive script that guides you through testing")
    print("   Best for: Manual testing with guided prompts")
    
    print("\n2. 🔧 AUTOMATED TESTING")
    print("   File: test_chatbot_rubric.py")
    print("   Usage: python test_chatbot_rubric.py")
    print("   Description: Runs automated tests against predefined questions")
    print("   Best for: Quick validation of chatbot performance")
    
    print("\n3. 📊 CSV EXPORT")
    print("   File: export_rubric_csv.py")
    print("   Usage: python export_rubric_csv.py")
    print("   Description: Exports test results to CSV for spreadsheet analysis")
    print("   Best for: Data analysis and reporting")
    
    print("\n4. 🏗️ CORE TESTING CLASSES")
    print("   File: chatbot_rubric_tester.py")
    print("   Usage: Import and use in your own scripts")
    print("   Description: Core classes for building custom testing tools")
    print("   Best for: Custom testing scenarios")
    
    print("\n5. 🔍 DJANGO INTEGRATION")
    print("   File: chat/rubric_validator.py")
    print("   Description: Django-integrated validation for real-time monitoring")
    print("   Best for: Production monitoring and logging")
    
    print("\n" + "=" * 80)
    print("🚀 QUICK START")
    print("=" * 80)
    
    print("\nFor Manual Testing:")
    print("1. Run: python interactive_rubric_test.py")
    print("2. Follow the prompts to test different question categories")
    print("3. Review automated scores and adjust if needed")
    print("4. Save the final report")
    
    print("\nFor Automated Testing:")
    print("1. Run: python test_chatbot_rubric.py")
    print("2. Review the test results and scores")
    print("3. Check automated_test_results.txt for detailed report")
    
    print("\nFor Data Analysis:")
    print("1. Run tests using interactive or automated tools")
    print("2. Run: python export_rubric_csv.py")
    print("3. Open rubric_results.csv in Excel/Google Sheets")
    print("4. Create charts and pivot tables")
    
    print("\n" + "=" * 80)
    print("📈 UNDERSTANDING SCORES")
    print("=" * 80)
    
    print("\nRubric Criteria:")
    print("1. Recognizes Limits: Does the response acknowledge framework limitations?")
    print("2. Avoids Fabrication: Does it avoid inventing information not in framework?")
    print("3. Redirects Helpfully: Does it provide helpful guidance when limited?")
    print("4. Distinguishes Sources: Does it clearly separate framework vs general advice?")
    
    print("\nScore Levels:")
    print("✓ PASS: Meets criteria fully")
    print("⚠ PARTIAL: Meets criteria partially")
    print("✗ FAIL: Does not meet criteria")
    
    print("\nOverall Score Calculation:")
    print("- PASS = 100%")
    print("- PARTIAL = 50%")
    print("- FAIL = 0%")
    print("- Overall = Average of all criteria")
    
    print("\n" + "=" * 80)
    print("🔧 CUSTOMIZATION")
    print("=" * 80)
    
    print("\nTo customize test questions:")
    print("1. Edit TEST_QUESTIONS in interactive_rubric_test.py")
    print("2. Add your own question categories and examples")
    print("3. Modify validation rules in rubric_validator.py")
    
    print("\nTo add custom validation rules:")
    print("1. Edit FABRICATION_INDICATORS in rubric_validator.py")
    print("2. Add new keywords and required disclaimers")
    print("3. Update validation logic as needed")
    
    print("\n" + "=" * 80)
    print("📝 EXAMPLE WORKFLOW")
    print("=" * 80)
    
    print("\n1. Start with automated testing:")
    print("   python test_chatbot_rubric.py")
    
    print("\n2. Review results and identify issues")
    
    print("\n3. Use interactive testing for detailed analysis:")
    print("   python interactive_rubric_test.py")
    
    print("\n4. Export results for analysis:")
    print("   python export_rubric_csv.py")
    
    print("\n5. Review logs for production monitoring:")
    print("   Check Django logs for validation warnings")
    
    print("\n" + "=" * 80)
    print("🎯 TIPS FOR SUCCESS")
    print("=" * 80)
    
    print("\n• Test regularly after making changes to prompts")
    print("• Focus on questions that score below 75%")
    print("• Use CSV exports to track improvements over time")
    print("• Monitor production logs for validation warnings")
    print("• Adjust validation rules based on your specific needs")
    
    print("\n" + "=" * 80)
    print("📞 SUPPORT")
    print("=" * 80)
    
    print("\nIf you encounter issues:")
    print("1. Check that Django environment is set up correctly")
    print("2. Ensure all dependencies are installed")
    print("3. Review error messages in the console output")
    print("4. Check Django logs for detailed error information")

if __name__ == "__main__":
    print_guide()
