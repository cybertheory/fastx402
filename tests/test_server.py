"""
Tests for x402 server functionality
"""

import pytest
from fastx402.server import X402Server
from fastx402.types import PaymentConfig, PaymentChallenge


def test_load_config_from_env(monkeypatch):
    """Test loading configuration from environment"""
    monkeypatch.setenv("X402_MERCHANT_ADDRESS", "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0")
    monkeypatch.setenv("X402_CHAIN_ID", "8453")
    monkeypatch.setenv("X402_CURRENCY", "USDC")
    monkeypatch.setenv("X402_MODE", "instant")
    
    server = X402Server()
    assert server.config.merchant_address == "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
    assert server.config.chain_id == 8453
    assert server.config.currency == "USDC"


def test_create_challenge():
    """Test creating payment challenge"""
    config = PaymentConfig(
        merchant_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
        chain_id=8453,
        currency="USDC"
    )
    server = X402Server(config=config)
    
    challenge = server.create_challenge(price="0.01")
    
    assert challenge.price == "0.01"
    assert challenge.currency == "USDC"
    assert challenge.chain_id == 8453
    assert challenge.merchant == config.merchant_address
    assert challenge.nonce is not None


def test_issue_402_response():
    """Test issuing 402 response"""
    config = PaymentConfig(
        merchant_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
        chain_id=8453,
        currency="USDC"
    )
    server = X402Server(config=config)
    
    challenge = server.create_challenge(price="0.01")
    response = server.issue_402_response(challenge)
    
    assert response.status_code == 402
    assert "challenge" in response.body.decode()

