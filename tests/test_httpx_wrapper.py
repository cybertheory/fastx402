"""
Tests for httpx wrapper
"""

import pytest
import httpx
from unittest.mock import Mock, AsyncMock
from fastx402.httpx_wrapper import X402HttpxClient


@pytest.fixture
def mock_402_response():
    """Mock 402 response with challenge"""
    response = Mock(spec=httpx.Response)
    response.status_code = 402
    response.json.return_value = {
        "error": "Payment Required",
        "challenge": {
            "price": "0.01",
            "currency": "USDC",
            "chain_id": 8453,
            "merchant": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "timestamp": 1699123456,
        }
    }
    return response


@pytest.fixture
def mock_success_response():
    """Mock success response"""
    response = Mock(spec=httpx.Response)
    response.status_code = 200
    response.json.return_value = {"msg": "success"}
    return response


def test_httpx_client_sync_handles_402(mock_402_response, mock_success_response):
    """Test sync httpx client handles 402"""
    def handle_x402(challenge):
        assert challenge["price"] == "0.01"
        return "signed_payment_header"
    
    client = X402HttpxClient(handle_x402=handle_x402)
    
    call_count = 0
    def mock_request(method, url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_402_response
        else:
            assert "X-PAYMENT" in kwargs.get("headers", {})
            return mock_success_response
    
    client._original_request = mock_request
    
    response = client.get("https://api.example.com/protected")
    
    assert response.status_code == 200
    assert call_count == 2


@pytest.mark.asyncio
async def test_httpx_client_async_handles_402(mock_402_response, mock_success_response):
    """Test async httpx client handles 402"""
    async def handle_x402(challenge):
        assert challenge["price"] == "0.01"
        return "signed_payment_header"
    
    client = X402HttpxClient(handle_x402=handle_x402)
    
    call_count = 0
    async def mock_request(method, url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_402_response
        else:
            assert "X-PAYMENT" in kwargs.get("headers", {})
            return mock_success_response
    
    client._original_request = mock_request
    
    response = await client.get("https://api.example.com/protected")
    
    assert response.status_code == 200
    assert call_count == 2


def test_httpx_client_preserves_headers(mock_402_response, mock_success_response):
    """Test that original headers are preserved"""
    def handle_x402(challenge):
        return "signed_payment_header"
    
    client = X402HttpxClient(handle_x402=handle_x402)
    
    original_headers = {"Authorization": "Bearer token123"}
    call_count = 0
    
    def mock_request(method, url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_402_response
        else:
            headers = kwargs.get("headers", {})
            assert headers.get("Authorization") == "Bearer token123"
            assert "X-PAYMENT" in headers
            return mock_success_response
    
    client._original_request = mock_request
    
    response = client.get(
        "https://api.example.com/protected",
        headers=original_headers
    )
    
    assert response.status_code == 200


def test_httpx_client_context_manager(mock_402_response):
    """Test context manager usage"""
    def handle_x402(challenge):
        return "signed_payment_header"
    
    mock_client = Mock(spec=httpx.Client)
    mock_client.close = Mock()
    
    with X402HttpxClient(handle_x402=handle_x402, client=mock_client) as client:
        assert client.client is mock_client
    
    mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_httpx_client_async_context_manager(mock_402_response):
    """Test async context manager usage"""
    async def handle_x402(challenge):
        return "signed_payment_header"
    
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.aclose = AsyncMock()
    
    async with X402HttpxClient(handle_x402=handle_x402, client=mock_client) as client:
        assert client.client is mock_client
    
    mock_client.aclose.assert_called_once()


