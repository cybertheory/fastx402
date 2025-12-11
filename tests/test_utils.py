"""
Tests for utility functions
"""

import pytest
from fastx402.utils import (
    get_eip712_domain,
    create_payment_message,
    generate_nonce,
    validate_address
)


def test_get_eip712_domain():
    """Test EIP-712 domain generation"""
    domain = get_eip712_domain(8453)
    
    assert domain["name"] == "x402"
    assert domain["version"] == "1"
    assert domain["chainId"] == 8453


def test_create_payment_message():
    """Test payment message creation"""
    challenge = {
        "price": "0.01",
        "currency": "USDC",
        "chain_id": 8453,
        "merchant": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
        "timestamp": 1699123456,
        "description": "Test payment"
    }
    
    message = create_payment_message(challenge)
    
    assert message["price"] == "0.01"
    assert message["currency"] == "USDC"
    assert message["chainId"] == 8453


def test_generate_nonce():
    """Test nonce generation"""
    nonce1 = generate_nonce()
    nonce2 = generate_nonce()
    
    assert nonce1 != nonce2
    assert len(nonce1) == 32  # 16 bytes = 32 hex chars


def test_validate_address():
    """Test address validation"""
    valid = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
    invalid = "not-an-address"
    
    assert validate_address(valid) is True
    assert validate_address(invalid) is False

