"""
Tests for x402 client functionality
"""

import pytest
import httpx
from unittest.mock import Mock, AsyncMock, patch
from fastx402.client import X402Client
from fastx402.types import PaymentChallenge


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
            "merchant": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            "timestamp": 1699123456,
            "description": "Test payment",
            "nonce": "test_nonce"
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


@pytest.mark.asyncio
async def test_client_handles_402_and_retries(mock_402_response, mock_success_response):
    """Test that client handles 402 and retries with payment"""
    call_count = 0
    
    async def mock_request(method, url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_402_response
        else:
            # Verify X-PAYMENT header was added
            assert "X-PAYMENT" in kwargs.get("headers", {})
            return mock_success_response
    
    client = X402Client(base_url="https://api.example.com")
    
    # Mock the client's request method
    with patch.object(client.client, 'request', side_effect=mock_request):
        # Mock _handle_402 to return payment data
        async def mock_handle_402(challenge, url):
            return {
                "signature": "0x1234",
                "signer": "0x5678",
                "challenge": challenge.model_dump() if hasattr(challenge, 'model_dump') else challenge
            }
        
        client._handle_402 = mock_handle_402
        
        response = await client.get("/protected")
        
        assert response.status_code == 200
        assert call_count == 2


@pytest.mark.asyncio
async def test_client_preserves_original_headers(mock_402_response, mock_success_response):
    """Test that client preserves original headers"""
    call_count = 0
    
    async def mock_request(method, url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_402_response
        else:
            headers = kwargs.get("headers", {})
            assert headers.get("Authorization") == "Bearer token123"
            assert "X-PAYMENT" in headers
            return mock_success_response
    
    client = X402Client(base_url="https://api.example.com")
    
    with patch.object(client.client, 'request', side_effect=mock_request):
        async def mock_handle_402(challenge, url):
            return {
                "signature": "0x1234",
                "signer": "0x5678",
                "challenge": challenge.model_dump() if hasattr(challenge, 'model_dump') else challenge
            }
        
        client._handle_402 = mock_handle_402
        
        response = await client.get(
            "/protected",
            headers={"Authorization": "Bearer token123"}
        )
        
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_client_returns_402_if_no_payment(mock_402_response):
    """Test that client returns 402 if payment handler returns None"""
    client = X402Client(base_url="https://api.example.com")
    
    with patch.object(client.client, 'request', return_value=mock_402_response):
        # _handle_402 returns None by default
        response = await client.get("/protected")
        
        assert response.status_code == 402


@pytest.mark.asyncio
async def test_client_handles_non_402_responses():
    """Test that client passes through non-402 responses"""
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"msg": "success"}
    
    client = X402Client(base_url="https://api.example.com")
    
    with patch.object(client.client, 'request', return_value=mock_response):
        response = await client.get("/public")
        
        assert response.status_code == 200
        assert response.json()["msg"] == "success"


@pytest.mark.asyncio
async def test_client_post_method():
    """Test POST method"""
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 200
    
    client = X402Client(base_url="https://api.example.com")
    
    with patch.object(client.client, 'request', return_value=mock_response) as mock_req:
        await client.post("/endpoint", json={"data": "test"})
        
        mock_req.assert_called_once()
        call_kwargs = mock_req.call_args[1]
        assert call_kwargs.get("json") == {"data": "test"}


@pytest.mark.asyncio
async def test_client_context_manager():
    """Test client as async context manager"""
    client = X402Client(base_url="https://api.example.com")
    
    async with client:
        assert client.client is not None
    
    # Client should be closed after context
    assert client.client.is_closed


@pytest.mark.asyncio
async def test_client_base_url_normalization():
    """Test that base URL is normalized"""
    client1 = X402Client(base_url="https://api.example.com/")
    client2 = X402Client(base_url="https://api.example.com")
    
    assert client1.base_url == client2.base_url
    assert client1.base_url == "https://api.example.com"

