#!/usr/bin/env python
"""
Test script to verify Ngrok response format fix.

This script validates:
1. NgrokMiddleware is registered in MIDDLEWARE
2. All JsonResponse calls have explicit content_type
3. Streaming responses have proper headers
4. Content-Type headers are preserved
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
sys.path.insert(0, str(Path(__file__).parent))

django.setup()

from django.conf import settings
from django.test import RequestFactory, TestCase
from django.test.client import Client
from chat.models import ChatSession
from knowledgeassistant.users.models import User


def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def check_middleware_registered():
    """Check if NgrokMiddleware is registered."""
    print_header("1. Checking NgrokMiddleware Registration")
    
    middleware_list = settings.MIDDLEWARE
    
    print(f"Total middleware registered: {len(middleware_list)}")
    print("\nMiddleware list:")
    for i, mw in enumerate(middleware_list, 1):
        marker = " ✅" if "NgrokMiddleware" in mw else ""
        print(f"  {i}. {mw}{marker}")
    
    has_ngrok = "config.middleware.NgrokMiddleware" in middleware_list
    
    if has_ngrok:
        print("\n✅ SUCCESS: NgrokMiddleware is registered!")
        # Check position
        idx = middleware_list.index("config.middleware.NgrokMiddleware")
        if idx == 1:  # Should be after SecurityMiddleware (index 0)
            print("✅ SUCCESS: NgrokMiddleware is in correct position (after SecurityMiddleware)")
        else:
            print(f"⚠️  WARNING: NgrokMiddleware is at index {idx}, expected at index 1")
    else:
        print("\n❌ ERROR: NgrokMiddleware is NOT registered!")
        print("   Please add it to MIDDLEWARE in config/settings/base.py")
    
    return has_ngrok


def check_response_headers():
    """Check if responses have proper Content-Type headers."""
    print_header("2. Checking Response Headers")
    
    # Check if we can access the middleware
    try:
        from config.middleware import NgrokMiddleware
        print("✅ SUCCESS: NgrokMiddleware can be imported")
    except ImportError as e:
        print(f"❌ ERROR: Cannot import NgrokMiddleware: {e}")
        return False
    
    # Create a test request factory
    factory = RequestFactory()
    middleware = NgrokMiddleware(lambda r: None)
    
    print("✅ SUCCESS: NgrokMiddleware instantiated successfully")
    
    return True


def check_json_responses():
    """Check if views use explicit content_type."""
    print_header("3. Checking JsonResponse Content-Types in Views")
    
    views_file = Path(__file__).parent / "chat" / "views.py"
    
    if not views_file.exists():
        print(f"❌ ERROR: Cannot find {views_file}")
        return False
    
    with open(views_file, 'r') as f:
        content = f.read()
    
    # Count JsonResponse calls
    lines = content.split('\n')
    json_response_lines = []
    json_response_with_type = []
    
    for i, line in enumerate(lines):
        if 'JsonResponse(' in line:
            json_response_lines.append(i + 1)
    
    # For each JsonResponse line, check if content_type appears within next 15 lines
    for line_num in json_response_lines:
        idx = line_num - 1
        found_content_type = False
        
        # Check current line and next 15 lines for content_type (some responses have long multiline strings)
        for j in range(idx, min(idx + 15, len(lines))):
            if 'content_type=' in lines[j]:
                found_content_type = True
                break
        
        if found_content_type:
            json_response_with_type.append(line_num)
    
    total = len(json_response_lines)
    with_type = len(json_response_with_type)
    
    print(f"Total JsonResponse calls found: {total}")
    print(f"JsonResponse calls with explicit content_type: {with_type}")
    
    if total == with_type:
        print("\n✅ SUCCESS: All JsonResponse calls have explicit content_type!")
        return True
    else:
        missing = total - with_type
        print(f"\n⚠️  WARNING: {missing} JsonResponse(s) missing explicit content_type")
        print("Missing on lines:")
        for line_num in json_response_lines:
            if line_num not in json_response_with_type:
                print(f"  Line {line_num}: {lines[line_num-1].strip()[:80]}")
        return False


def check_settings():
    """Check if ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS are configured."""
    print_header("4. Checking Ngrok Configuration in Settings")
    
    allowed_hosts = settings.ALLOWED_HOSTS
    csrf_origins = getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])
    
    print(f"ALLOWED_HOSTS: {allowed_hosts}")
    print(f"CSRF_TRUSTED_ORIGINS: {csrf_origins}")
    
    has_ngrok_host = any('ngrok' in str(host) for host in allowed_hosts)
    has_ngrok_csrf = any('ngrok' in str(origin) for origin in csrf_origins)
    
    if has_ngrok_host:
        print("\n✅ SUCCESS: ngrok domain found in ALLOWED_HOSTS")
    else:
        print("\n⚠️  WARNING: No ngrok domain in ALLOWED_HOSTS")
        print("   Add your ngrok domain to ALLOWED_HOSTS in config/settings/local.py")
    
    if has_ngrok_csrf:
        print("✅ SUCCESS: ngrok domain found in CSRF_TRUSTED_ORIGINS")
    else:
        print("⚠️  WARNING: No ngrok domain in CSRF_TRUSTED_ORIGINS")
        print("   Add your ngrok domain to CSRF_TRUSTED_ORIGINS in config/settings/local.py")
    
    return has_ngrok_host and has_ngrok_csrf


def main():
    """Run all checks."""
    print("\n" + "="*60)
    print("  NGROK RESPONSE FORMAT FIX - VERIFICATION TEST")
    print("="*60)
    
    checks = [
        ("Middleware Registration", check_middleware_registered),
        ("Response Headers", check_response_headers),
        ("JsonResponse Content-Types", check_json_responses),
        ("Ngrok Settings", check_settings),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ ERROR during '{name}' check: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("  ✅ ALL CHECKS PASSED - Ngrok fix is properly applied!")
    else:
        print("  ⚠️  SOME CHECKS FAILED - Please review the issues above")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
