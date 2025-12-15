#!/usr/bin/env python3
"""
MCP Verification Test Script

This script helps verify that MCP (OAuth Identity Passthrough) is working correctly.
Run this from the backend directory after starting the server.

Usage:
    python verify_mcp.py
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000/api"
HEALTH_ENDPOINT = f"{BASE_URL}/health"
MCP_CONFIG_ENDPOINT = f"{BASE_URL}/mcp-config"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(message):
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")

def print_error(message):
    print(f"{Colors.RED}✗{Colors.RESET} {message}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def check_mcp_config():
    """Check MCP configuration status"""
    print_header("STEP 1: MCP Configuration Check")
    
    try:
        response = requests.get(MCP_CONFIG_ENDPOINT, timeout=5)
        response.raise_for_status()
        config = response.json()
        
        print_info("MCP Configuration Response:")
        print(json.dumps(config, indent=2))
        
        if config.get("mcp_enabled"):
            print_success("MCP is ENABLED in configuration")
            return True
        else:
            print_error("MCP is DISABLED - set MCP_ENABLED=True in .env")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to backend at {BASE_URL}")
        print_warning("Make sure backend is running on localhost:8000")
        return False
    except Exception as e:
        print_error(f"Error checking MCP config: {str(e)}")
        return False

def check_health():
    """Check health endpoint for MCP status"""
    print_header("STEP 2: Health Check")
    
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        response.raise_for_status()
        health = response.json()
        
        print_info("Health Status:")
        print(json.dumps(health, indent=2))
        
        if health.get("mcp_enabled"):
            print_success("MCP is ENABLED in health check")
            return True
        else:
            print_error("MCP is DISABLED in health check")
            return False
            
    except Exception as e:
        print_error(f"Error checking health: {str(e)}")
        return False

def check_backend_logs():
    """Guide user to check backend logs"""
    print_header("STEP 3: Backend Logs Verification")
    
    print_info("To complete MCP verification, follow these steps:")
    print("  1. Send a chat message from the UI")
    print("  2. Check backend console/logs for these messages:")
    print()
    
    print_warning("Look for: '═══ MCP CONTEXT AT ENDPOINT ═══'")
    print("  This confirms MCP context is received at the endpoint")
    print()
    
    print_warning("Look for: '✓ MCP ENABLED AND CONFIGURED'")
    print("  This confirms MCP headers are being set")
    print()
    
    print_warning("Look for: 'X-User-Id Header: {user-id}'")
    print("           'X-User-Email Header: {user-email}'")
    print("  This confirms user identity headers are being added")
    print()
    
    print_warning("Look for: 'Request headers being sent: {...'X-User-Id'...'X-User-Email'...}'")
    print("  This confirms headers are in the actual HTTP request")
    print()

def main():
    print(f"\n{Colors.BOLD}MCP (OAuth Identity Passthrough) Verification{Colors.RESET}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {
        "mcp_config": check_mcp_config(),
        "health": check_health(),
    }
    
    check_backend_logs()
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    if results["mcp_config"] and results["health"]:
        print_success("MCP Configuration: ENABLED")
        print_success("Health Check: ENABLED")
        print()
        print_success("MCP is properly configured!")
        print_info("Next: Send a message and verify log patterns above")
        return 0
    else:
        print_error("MCP Configuration check failed")
        print_info("Check .env file and ensure MCP_ENABLED=True")
        return 1

if __name__ == "__main__":
    sys.exit(main())
