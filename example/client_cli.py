#!/usr/bin/env python3
"""
Full-featured CLI client for fastx402
Handles payment challenges, wallet signing, and request retries
"""

import asyncio
import json
import sys
import argparse
from typing import Optional, Dict, Any
import httpx
from eth_account import Account
from fastx402.client import X402Client
from fastx402.types import PaymentChallenge, PaymentSignature
from fastx402.utils import (
    get_eip712_domain,
    get_eip712_types,
    create_payment_message,
    encode_payment_message
)


class WalletSigner:
    """Simple wallet signer using private key"""
    
    def __init__(self, private_key: Optional[str] = None):
        """
        Initialize wallet signer
        
        Args:
            private_key: Private key hex string (with or without 0x prefix)
                        If None, will prompt user or use environment variable
        """
        if private_key is None:
            private_key = self._load_private_key()
        
        # Remove 0x prefix if present
        if private_key.startswith("0x"):
            private_key = private_key[2:]
        
        self.account = Account.from_key(private_key)
        self.address = self.account.address
    
    @staticmethod
    def _load_private_key() -> str:
        """Load private key from environment or prompt user"""
        import os
        private_key = os.getenv("PRIVATE_KEY")
        
        if not private_key:
            print("[WARNING] No private key found in environment (PRIVATE_KEY)")
            print("   For testing, you can set it with: export PRIVATE_KEY=your_key")
            print("   Or enter it when prompted (not recommended for production)")
            private_key = input("Enter private key (hex, with or without 0x): ").strip()
        
        if not private_key:
            raise ValueError("Private key is required")
        
        return private_key
    
    def sign_payment_challenge(self, challenge: PaymentChallenge) -> PaymentSignature:
        """
        Sign a payment challenge using EIP-712
        
        Args:
            challenge: Payment challenge from server
            
        Returns:
            PaymentSignature with signature
        """
        from eth_account.messages import encode_typed_data
        
        domain = get_eip712_domain(challenge.chain_id)
        types = get_eip712_types()
        # Use model_dump() for Pydantic v2, fallback to dict() for v1
        challenge_dict = challenge.model_dump() if hasattr(challenge, 'model_dump') else challenge.dict()
        message = create_payment_message(challenge_dict)
        
        # Create structured data
        structured_data = {
            "types": types,
            "domain": domain,
            "primaryType": "Payment",
            "message": message
        }
        
        # Sign using eth_account
        encoded = encode_typed_data(structured_data)
        signature = Account.sign_message(encoded, self.account.key).signature.hex()
        
        return PaymentSignature(
            signature=signature,
            signer=self.address,
            challenge=challenge
        )


class EnhancedX402Client(X402Client):
    """Enhanced client with wallet signing capability"""
    
    def __init__(self, base_url: str, signer: Optional[WalletSigner] = None, rpc_url: Optional[str] = None):
        """
        Initialize enhanced client
        
        Args:
            base_url: Base URL for API
            signer: Optional wallet signer (will create one if not provided and no rpc_url)
            rpc_url: Optional RPC URL for frontend signing (if None, uses local signer)
        """
        # Create RPC handler if signer is provided and no RPC URL
        rpc_handler = None
        if not rpc_url:
            # Use local signer
            if signer is None:
                signer = WalletSigner()
            
            async def handle_402(challenge: PaymentChallenge) -> Optional[PaymentSignature]:
                return self._sign_challenge(challenge)
            rpc_handler = handle_402
        
        super().__init__(
            base_url=base_url,
            rpc_url=rpc_url,
            rpc_handler=rpc_handler
        )
        self.signer = signer
    
    def _sign_challenge(self, challenge: PaymentChallenge) -> PaymentSignature:
        """
        Sign a payment challenge using the wallet signer
        
        Args:
            challenge: Payment challenge
            
        Returns:
            PaymentSignature with signature
        """
        print(f"\n{'='*60}")
        print("Payment Required")
        print(f"{'='*60}")
        print(f"Price:     {challenge.price} {challenge.currency}")
        print(f"Chain ID:  {challenge.chain_id}")
        print(f"Merchant:  {challenge.merchant}")
        if challenge.description:
            print(f"Description: {challenge.description}")
        print(f"\nSigning address: {self.signer.address}")
        
        # Sign the challenge
        print("\nSigning payment challenge...")
        signature = self.signer.sign_payment_challenge(challenge)
        
        if not signature:
            raise ValueError("Failed to sign payment challenge")
        
        print("[OK] Payment signed successfully!")
        print(f"Signature: {signature.signature[:20]}...")
        print(f"{'='*60}\n")
        
        return signature


async def make_request(
    client: EnhancedX402Client,
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None
):
    """Make a request and handle response"""
    print(f"\nMaking {method} request to {endpoint}...")
    
    try:
        if method.upper() == "GET":
            response = await client.get(endpoint)
        elif method.upper() == "POST":
            response = await client.post(endpoint, json=data)
        else:
            print(f"[ERROR] Unsupported method: {method}")
            return
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("[OK] Success!")
            print(json.dumps(result, indent=2))
        elif response.status_code == 402:
            print("[ERROR] Still received 402 after payment attempt")
            result = response.json()
            print(json.dumps(result, indent=2))
        else:
            print(f"[ERROR] Error: {response.status_code}")
            try:
                result = response.json()
                print(json.dumps(result, indent=2))
            except:
                print(response.text)
    
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="fastx402 CLI Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Make a free request
  python client_cli.py get /free
  
  # Make a paid request
  python client_cli.py get /paid
  
  # Make a POST request
  python client_cli.py post /api/submit --data '{"name": "test"}'
  
  # Use custom private key
  python client_cli.py get /paid --key 0x1234...
        """
    )
    
    parser.add_argument(
        "method",
        choices=["get", "post", "GET", "POST"],
        help="HTTP method"
    )
    
    parser.add_argument(
        "endpoint",
        help="API endpoint (e.g., /free, /paid, /premium)"
    )
    
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL for API (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--key",
        help="Private key for signing (or set PRIVATE_KEY env var)"
    )
    
    parser.add_argument(
        "--data",
        help="JSON data for POST requests"
    )
    
    args = parser.parse_args()
    
    # Normalize endpoint path (handle Windows path conversion in Git Bash)
    endpoint = args.endpoint
    if not endpoint.startswith('/'):
        # If it looks like a Windows path, extract just the filename
        if ':' in endpoint or '\\' in endpoint:
            # Extract the last part after / or \
            endpoint = '/' + endpoint.replace('\\', '/').split('/')[-1]
        else:
            endpoint = '/' + endpoint.lstrip('/')
    
    # Parse JSON data if provided
    data = None
    if args.data:
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            print(f"[ERROR] Invalid JSON data: {args.data}")
            sys.exit(1)
    
    # Create signer (only if not using RPC URL)
    signer = None
    if not args.rpc_url:
        try:
            signer = WalletSigner(private_key=args.key)
        except Exception as e:
            print(f"[ERROR] Failed to initialize wallet: {str(e)}")
            sys.exit(1)
    
    # Create client
    client = EnhancedX402Client(
        base_url=args.url,
        signer=signer,
        rpc_url=args.rpc_url
    )
    
    if args.rpc_url:
        print(f"[INFO] Using RPC URL: {args.rpc_url}")
        print("[INFO] Payment challenges will be sent to frontend for signing")
    
    try:
        await make_request(client, args.method, endpoint, data)
    finally:
        await client.close()


if __name__ == "__main__":
    print("fastx402 CLI Client")
    print("=" * 60)
    asyncio.run(main())

