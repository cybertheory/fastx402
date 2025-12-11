"""
Utility functions for EIP-712 encoding, hex/base64 conversion, etc.
"""

import json
from typing import Dict, Any
from eth_account.messages import encode_defunct, _hash_eip191_message
from eth_utils import to_checksum_address, is_address
import hashlib


def get_eip712_domain(chain_id: int) -> Dict[str, Any]:
    """Get EIP-712 domain separator for x402 payments"""
    return {
        "name": "x402",
        "version": "1",
        "chainId": chain_id,
        "verifyingContract": "0x0000000000000000000000000000000000000000"
    }


def get_eip712_types() -> Dict[str, Any]:
    """Get EIP-712 type definitions for payment message"""
    return {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"}
        ],
        "Payment": [
            {"name": "price", "type": "string"},
            {"name": "currency", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "merchant", "type": "address"},
            {"name": "timestamp", "type": "uint256"},
            {"name": "description", "type": "string"},
        ]
    }


def create_payment_message(challenge: Dict[str, Any]) -> Dict[str, Any]:
    """Create EIP-712 payment message from challenge"""
    merchant = challenge["merchant"]
    # Convert to checksum address
    # Handle both checksum and lowercase addresses
    try:
        # If already looks like checksum (mixed case), try to use as-is first
        if merchant != merchant.lower() and merchant != merchant.upper():
            # Might already be checksum, validate it
            try:
                merchant_checksum = to_checksum_address(merchant.lower())
            except:
                # If validation fails, use as-is (might be valid checksum)
                merchant_checksum = merchant
        else:
            # Lowercase or uppercase, convert to checksum
            merchant_lower = merchant.lower() if merchant.startswith("0x") else "0x" + merchant.lower()
            merchant_checksum = to_checksum_address(merchant_lower)
    except Exception:
        # Fallback: use address as-is if conversion fails
        merchant_checksum = merchant if merchant.startswith("0x") else "0x" + merchant
    
    return {
        "price": str(challenge["price"]),
        "currency": challenge["currency"],
        "chainId": challenge["chain_id"],
        "merchant": merchant_checksum,
        "timestamp": challenge["timestamp"],
        "description": challenge.get("description", ""),
    }


def encode_payment_message(challenge: Dict[str, Any]) -> bytes:
    """Encode payment challenge as EIP-712 message"""
    from eth_account.messages import encode_typed_data, _hash_eip191_message
    
    domain = get_eip712_domain(challenge["chain_id"])
    types = get_eip712_types()
    message = create_payment_message(challenge)
    
    # Create structured data
    structured_data = {
        "types": types,
        "domain": domain,
        "primaryType": "Payment",
        "message": message
    }
    
    # Encode using eth_account
    encoded = encode_typed_data(structured_data)
    # Hash the encoded message
    message_hash = _hash_eip191_message(encoded)
    return message_hash


def verify_signature(signature: str, message_hash: bytes, signer: str) -> bool:
    """Verify EIP-712 signature"""
    from eth_account import Account
    from eth_account.messages import encode_defunct
    
    try:
        # Recover signer from signature
        recovered = Account.recover_message(
            encode_defunct(message_hash),
            signature=signature
        )
        return recovered.lower() == signer.lower()
    except Exception:
        return False


def generate_nonce() -> str:
    """Generate a random nonce for replay protection"""
    import secrets
    return secrets.token_hex(16)


def validate_address(address: str) -> bool:
    """Validate Ethereum address format"""
    return is_address(address)


def to_hex(data: bytes) -> str:
    """Convert bytes to hex string with 0x prefix"""
    return "0x" + data.hex()


def from_hex(hex_str: str) -> bytes:
    """Convert hex string to bytes"""
    if hex_str.startswith("0x"):
        hex_str = hex_str[2:]
    return bytes.fromhex(hex_str)

