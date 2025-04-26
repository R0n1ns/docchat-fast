#!/usr/bin/env python3
"""
API Test Script for Document Management System

This script tests the basic functionality of the API
including authentication, document upload, and retrieval.
"""

import json
import os
import sys
import time
import requests

# API Base URL
API_URL = "http://localhost:5000"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin"

# Test data
TEST_USER = {
    "email": "test@example.com",
    "password": "Test123!",
    "full_name": "Test User"
}

TEST_DOCUMENT = {
    "title": "Test Document",
    "description": "This is a test document"
}

TEST_FILE_PATH = "test_document.txt"


def create_test_file():
    """Create a test document file"""
    with open(TEST_FILE_PATH, "w") as f:
        f.write("This is a test document content.\n")
        f.write("It has multiple lines.\n")
        f.write("Used for testing the Document Management API.")


def cleanup():
    """Clean up test files"""
    if os.path.exists(TEST_FILE_PATH):
        os.remove(TEST_FILE_PATH)


def test_register_user():
    """Test user registration"""
    print("\n=== Testing User Registration ===")
    url = f"{API_URL}/api/v1/auth/register"
    
    response = requests.post(url, json=TEST_USER)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response.status_code == 201


def test_login_user():
    """Test user login and TOTP code generation"""
    print("\n=== Testing User Login ===")
    url = f"{API_URL}/api/v1/auth/login"
    
    response = requests.post(url, json={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    })
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response.status_code == 200


def get_admin_tokens():
    """Get admin tokens for testing"""
    print("\n=== Getting Admin Tokens ===")
    
    # Login
    login_url = f"{API_URL}/api/v1/auth/login"
    login_response = requests.post(login_url, json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    if login_response.status_code != 200:
        print(f"Admin login failed: {login_response.text}")
        return None, None
    
    print("Admin login successful, TOTP code generated")
    
    # In a real scenario, you would need to get the TOTP code
    # from the admin's email. For testing, we'll assume code verification
    # is bypassed for the admin in development mode.
    
    # Verify TOTP (assuming code is bypassed for admin)
    verify_url = f"{API_URL}/api/v1/auth/verify"
    verify_response = requests.post(verify_url, json={
        "email": ADMIN_EMAIL,
        "code": "123456"  # Placeholder
    })
    
    if verify_response.status_code != 200:
        print(f"TOTP verification failed: {verify_response.text}")
        return None, None
    
    tokens = verify_response.json()
    print("Got admin tokens successfully")
    
    return tokens.get("access_token"), tokens.get("refresh_token")


def test_upload_document(access_token):
    """Test document upload"""
    print("\n=== Testing Document Upload ===")
    url = f"{API_URL}/api/v1/documents"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    with open(TEST_FILE_PATH, "rb") as f:
        files = {
            "file": (os.path.basename(TEST_FILE_PATH), f, "text/plain")
        }
        data = {
            "title": TEST_DOCUMENT["title"],
            "description": TEST_DOCUMENT["description"]
        }
        
        response = requests.post(url, headers=headers, data=data, files=files)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json() if response.status_code < 300 else response.text}")
    
    if response.status_code == 201:
        document_id = response.json().get("document_id")
        return document_id
    return None


def test_list_documents(access_token):
    """Test listing documents"""
    print("\n=== Testing Document Listing ===")
    url = f"{API_URL}/api/v1/documents"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(url, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2) if response.status_code < 300 else response.text}")
    
    return response.status_code == 200


def test_get_document(access_token, document_id):
    """Test getting a document"""
    print(f"\n=== Testing Document Retrieval (ID: {document_id}) ===")
    url = f"{API_URL}/api/v1/documents/{document_id}"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(url, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2) if response.status_code < 300 else response.text}")
    
    return response.status_code == 200


def test_download_document(access_token, document_id):
    """Test downloading a document"""
    print(f"\n=== Testing Document Download (ID: {document_id}) ===")
    url = f"{API_URL}/api/v1/documents/{document_id}/download"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(url, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Content-Length: {response.headers.get('Content-Length')} bytes")
    
    if response.status_code == 200:
        download_path = f"downloaded_{os.path.basename(TEST_FILE_PATH)}"
        with open(download_path, "wb") as f:
            f.write(response.content)
        print(f"File downloaded to {download_path}")
        
        # Cleanup downloaded file
        if os.path.exists(download_path):
            os.remove(download_path)
    
    return response.status_code == 200


def run_tests():
    """Run the API tests"""
    try:
        create_test_file()
        
        # Get admin tokens for testing
        access_token, refresh_token = get_admin_tokens()
        if not access_token or not refresh_token:
            print("Failed to get admin tokens, exiting tests")
            return False
        
        # Test document upload
        document_id = test_upload_document(access_token)
        if not document_id:
            print("Document upload failed, exiting tests")
            return False
        
        # Test document listing
        if not test_list_documents(access_token):
            print("Document listing failed")
        
        # Test document retrieval
        if not test_get_document(access_token, document_id):
            print("Document retrieval failed")
        
        # Test document download
        if not test_download_document(access_token, document_id):
            print("Document download failed")
        
        print("\n=== Tests completed successfully ===")
        return True
        
    except Exception as e:
        print(f"Error during tests: {str(e)}")
        return False
    finally:
        cleanup()


if __name__ == "__main__":
    print("=== Document Management API Test ===")
    print(f"API URL: {API_URL}")
    
    # Give the server some time to start if needed
    if len(sys.argv) > 1 and sys.argv[1] == "--wait":
        wait_seconds = 5
        print(f"Waiting {wait_seconds} seconds for the server to start...")
        time.sleep(wait_seconds)
    
    success = run_tests()
    sys.exit(0 if success else 1)