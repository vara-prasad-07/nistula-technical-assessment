"""
Test Script
==========================================
This script loads test data from test_data.json and makes HTTP requests
to the webhook endpoint for each message. Results are printed in a readable format.

Usage:
    1. Ensure the FastAPI server is running: uvicorn main:app --reload
    2. Run this script: python test_runner.py
    3. View all responses with confidence scores and actions
"""

import json
import requests
import time
from datetime import datetime
from typing import List, Dict, Any

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"
WEBHOOK_ENDPOINT = f"{API_BASE_URL}/webhook/message"
TEST_DATA_FILE = "test_data.json"

# Color codes for terminal output (optional, for readability)
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def load_test_data(file_path: str) -> List[Dict[str, Any]]:
    """Load test data from JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        print(f"{Colors.GREEN}✓ Loaded {len(data)} test messages from {file_path}{Colors.ENDC}\n")
        return data
    except FileNotFoundError:
        print(f"{Colors.RED}✗ Error: {file_path} not found{Colors.ENDC}")
        return []
    except json.JSONDecodeError:
        print(f"{Colors.RED}✗ Error: Invalid JSON in {file_path}{Colors.ENDC}")
        return []

def check_server_health() -> bool:
    """Check if the API server is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print(f"{Colors.GREEN}✓ Server is running and healthy{Colors.ENDC}\n")
            return True
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}✗ Error: Cannot connect to {API_BASE_URL}{Colors.ENDC}")
        print(f"   Make sure FastAPI is running: uvicorn main:app --reload\n")
        return False
    except requests.exceptions.Timeout:
        print(f"{Colors.RED}✗ Error: Server timeout{Colors.ENDC}\n")
        return False

def send_message(message_data: Dict[str, Any], test_number: int, total_tests: int) -> Dict[str, Any]:
    """
    Send a single message to the webhook endpoint.
    Returns the response from the server.
    """
    try:
        response = requests.post(WEBHOOK_ENDPOINT, json=message_data, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"HTTP {response.status_code}",
                "detail": response.text
            }
    except requests.exceptions.Timeout:
        return {"error": "Request timeout"}
    except requests.exceptions.ConnectionError:
        return {"error": "Connection failed"}
    except Exception as e:
        return {"error": str(e)}

def print_test_result(test_number: int, total_tests: int, message_data: Dict[str, Any], 
                      response: Dict[str, Any]) -> None:
    """Print formatted test result."""
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}Test {test_number}/{total_tests}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}\n")
    
    # Input Message
    print(f"{Colors.BOLD}INPUT MESSAGE:{Colors.ENDC}")
    print(f"  Channel:    {message_data.get('source', 'N/A')}")
    print(f"  Guest:      {message_data.get('guest_name', 'N/A')}")
    print(f"  Message:    {message_data.get('message', 'N/A')}")
    print(f"  Booking:    {message_data.get('booking_ref', 'N/A')}")
    print(f"  Timestamp:  {message_data.get('timestamp', 'N/A')}\n")
    
    # Response
    if "error" in response:
        print(f"{Colors.RED}{Colors.BOLD}ERROR:{Colors.ENDC}")
        print(f"  {response['error']}")
        if "detail" in response:
            print(f"  {response['detail']}")
    else:
        print(f"{Colors.BOLD}AI RESPONSE:{Colors.ENDC}")
        print(f"  Message ID:        {response.get('message_id', 'N/A')[:8]}...")
        print(f"  Query Type:        {Colors.YELLOW}{response.get('query_type', 'N/A')}{Colors.ENDC}")
        print(f"  Drafted Reply:     {response.get('drafted_reply', 'N/A')}")
        
        # Confidence score with color coding
        confidence = response.get('confidence_score', 0)
        if confidence >= 0.85:
            confidence_color = Colors.GREEN
            confidence_label = "HIGH"
        elif confidence >= 0.60:
            confidence_color = Colors.YELLOW
            confidence_label = "MEDIUM"
        else:
            confidence_color = Colors.RED
            confidence_label = "LOW"
        
        print(f"  Confidence Score:  {confidence_color}{confidence} ({confidence_label}){Colors.ENDC}")
        
        # Action with color coding
        action = response.get('action', 'N/A')
        if action == "auto_send":
            action_color = Colors.GREEN
        elif action == "agent_review":
            action_color = Colors.YELLOW
        else:  # escalate
            action_color = Colors.RED
        
        print(f"  Action:            {action_color}{action.upper()}{Colors.ENDC}")
    
    print()

def print_summary(results: List[Dict[str, Any]]) -> None:
    """Print test summary statistics."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}SUMMARY{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}\n")
    
    total = len(results)
    auto_send = sum(1 for r in results if r.get('action') == 'auto_send' and 'error' not in r)
    agent_review = sum(1 for r in results if r.get('action') == 'agent_review' and 'error' not in r)
    escalate = sum(1 for r in results if r.get('action') == 'escalate' and 'error' not in r)
    errors = sum(1 for r in results if 'error' in r)
    
    print(f"Total Tests:        {total}")
    print(f"{Colors.GREEN}Auto Send:        {auto_send}{Colors.ENDC}")
    print(f"{Colors.YELLOW}Agent Review:     {agent_review}{Colors.ENDC}")
    print(f"{Colors.RED}Escalate:         {escalate}{Colors.ENDC}")
    print(f"{Colors.RED}Errors:           {errors}{Colors.ENDC}\n")
    
    # Average confidence
    confidences = [r.get('confidence_score', 0) for r in results if 'error' not in r]
    if confidences:
        avg_confidence = sum(confidences) / len(confidences)
        print(f"Average Confidence: {avg_confidence:.2f}\n")

def main():
    """Main test runner function."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "NISTULA MESSAGING PLATFORM - TEST RUNNER" + " "*18 + "║")
    print("╚" + "="*78 + "╝")
    print(f"{Colors.ENDC}\n")
    
    # Check server health
    if not check_server_health():
        return
    
    # Load test data
    test_messages = load_test_data(TEST_DATA_FILE)
    if not test_messages:
        return
    
    # Run tests
    results = []
    for i, message_data in enumerate(test_messages, 1):
        response = send_message(message_data, i, len(test_messages))
        results.append(response)
        print_test_result(i, len(test_messages), message_data, response)
        time.sleep(0.5)  # Small delay between requests
    
    # Print summary
    print_summary(results)
    
    print(f"{Colors.GREEN}✓ All tests completed{Colors.ENDC}\n")

if __name__ == "__main__":
    main()
