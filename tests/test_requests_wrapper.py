"""
Tests for requests wrapper
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from fastx402.requests_wrapper import patch_requests, X402Session


@pytest.fixture
def mock_402_response():
    """Mock 402 response with challenge"""
    response = Mock(spec=requests.Response)
    response.status_code = 402
    response.json.return_value = {
        "error": "Payment Required",
        "challenge": {
            "price": "0.01",
            "currency": "USDC",
            "chain_id": 8453,
            "merchant": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            "timestamp": 1699123456,
            "description": "Test payment"
        }
    }
    return response


@pytest.fixture
def mock_success_response():
    """Mock success response"""
    response = Mock(spec=requests.Response)
    response.status_code = 200
    response.json.return_value = {"msg": "success"}
    return response


def test_patch_requests_handles_402(mock_402_response, mock_success_response):
    """Test that patched session handles 402 and retries"""
    def handle_x402(challenge):
        assert challenge["price"] == "0.01"
        return "signed_payment_header"
    
    # Create a session and mock request BEFORE patching
    session = requests.Session()
    call_count = 0
    
    def mock_request(method, url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_402_response
        else:
            # Verify X-PAYMENT header was added
            assert "X-PAYMENT" in kwargs.get("headers", {})
            return mock_success_response
    
    # Replace request BEFORE patching (so patch_requests captures our mock)
    session.request = mock_request
    
    # Now patch it - patch_requests will capture our mock_request as original_request
    patched_session = patch_requests(handle_x402=handle_x402, session=session)
    
    response = patched_session.get("https://api.example.com/protected")
    
    assert response.status_code == 200
    assert call_count == 2  # Should retry once


def test_patch_requests_preserves_headers(mock_402_response, mock_success_response):
    """Test that original headers are preserved"""
    def handle_x402(challenge):
        return "signed_payment_header"
    
    # Create session with mock request BEFORE patching
    session = requests.Session()
    original_headers = {"Authorization": "Bearer token123"}
    call_count = 0
    
    def mock_request(method, url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_402_response
        else:
            headers = kwargs.get("headers", {})
            # Original header should be preserved
            assert headers.get("Authorization") == "Bearer token123"
            # X-PAYMENT should be added
            assert "X-PAYMENT" in headers
            return mock_success_response
    
    # Mock request BEFORE patching
    session.request = mock_request
    
    # Patch the session
    patched_session = patch_requests(handle_x402=handle_x402, session=session)
    
    response = patched_session.get(
        "https://api.example.com/protected",
        headers=original_headers
    )
    
    assert response.status_code == 200


def test_patch_requests_no_handler_return(mock_402_response):
    """Test that 402 is returned if handler returns None"""
    def handle_x402(challenge):
        return None
    
    session = patch_requests(handle_x402=handle_x402)
    session.request = lambda *args, **kwargs: mock_402_response
    
    response = session.get("https://api.example.com/protected")
    
    assert response.status_code == 402


def test_x402_session_class(mock_402_response, mock_success_response):
    """Test X402Session class"""
    def handle_x402(challenge):
        return "signed_payment_header"
    
    session = X402Session(handle_x402=handle_x402)
    
    call_count = 0
    def mock_request(method, url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_402_response
        else:
            assert "X-PAYMENT" in kwargs.get("headers", {})
            return mock_success_response
    
    session._original_request = mock_request
    
    response = session.get("https://api.example.com/protected")
    
    assert response.status_code == 200
    assert call_count == 2


def test_patch_requests_with_existing_session():
    """Test patching an existing session"""
    existing_session = requests.Session()
    def handle_x402(challenge):
        return "signed_payment_header"
    
    patched = patch_requests(handle_x402=handle_x402, session=existing_session)
    
    assert patched is existing_session
    # Verify the request method was replaced
    assert callable(patched.request)
    # The request method should be the patched version (not the original)
    assert patched.request != requests.Session.request

