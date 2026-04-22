#!/usr/bin/env python3
"""Test stealth configuration"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, '.')

print('Testing stealth_config.py...')
print('='*60)

try:
    from common.stealth_config import (
        StealthStrategy,
        BrowserFingerprint,
        get_random_delay,
        get_typing_delay,
        USER_AGENTS_THAI,
        STEALTH_SCRIPTS,
    )
    print('All imports successful')
    
    # Test random delay
    delay = get_random_delay(100, 500)
    print(f'Random delay: {delay:.3f}s')
    
    # Test typing delay
    typing_delay = get_typing_delay()
    print(f'Typing delay: {typing_delay:.3f}s')
    
    # Test user agent
    ua = USER_AGENTS_THAI[0]
    print(f'User agent: {ua[:50]}...')
    
    # Test stealth script length
    script = StealthStrategy.get_init_script()
    print(f'Stealth script length: {len(script)} chars')
    
    # Test browser fingerprint
    fp = BrowserFingerprint.random()
    print(f'Random fingerprint - UA: {fp.user_agent[:40]}...')
    print(f'Viewport: {fp.viewport}')
    
    print()
    print('='*60)
    print('All stealth config tests PASSED!')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
