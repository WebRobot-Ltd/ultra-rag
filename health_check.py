#!/usr/bin/env python3
"""
UltraRAG Health Check Script
"""
import sys

try:
    # Test import di ultrarag
    import ultrarag
    print("UltraRAG health check: OK")
    sys.exit(0)
except ImportError as e:
    print(f"UltraRAG health check: FAILED - Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"UltraRAG health check: FAILED - {e}")
    sys.exit(1)
