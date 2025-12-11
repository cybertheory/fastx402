"""
Privy WAAS provider implementation
"""

import httpx
from typing import Optional
from fastx402.waas.base import WAASProvider
from fastx402.types import PaymentChallenge, PaymentVerificationResult
from fastx402.utils import verify_signature, encode_payment_message


class PrivyProvider(WAASProvider):
    """Privy wallet-as-a-service provider"""
    
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        base_url: str = "https://auth.privy.io"
    ):
        """
        Initialize Privy provider
        
        Args:
            app_id: Privy application ID
            app_secret: Privy application secret
            base_url: Privy API base URL
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def verify_payment(
        self,
        challenge: PaymentChallenge,
        signature: str,
        signer: str
    ) -> PaymentVerificationResult:
        """Verify payment signature via Privy"""
        try:
            # Encode the message
            message_hash = encode_payment_message(challenge.dict())
            
            # Verify signature locally
            is_valid = verify_signature(signature, message_hash, signer)
            
            if not is_valid:
                return PaymentVerificationResult(
                    valid=False,
                    error="Invalid signature"
                )
            
            # Optionally verify with Privy API
            # For now, we rely on local verification
            return PaymentVerificationResult(
                valid=True,
                signer=signer
            )
        except Exception as e:
            return PaymentVerificationResult(
                valid=False,
                error=str(e)
            )
    
    async def get_wallet_address(
        self,
        user_id: str
    ) -> Optional[str]:
        """Get wallet address for Privy user"""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/users/{user_id}",
                headers={
                    "Authorization": f"Bearer {self.app_secret}",
                    "privy-app-id": self.app_id
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract wallet address from Privy user data
            wallets = data.get("wallets", [])
            if wallets:
                return wallets[0].get("address")
            return None
        except Exception:
            return None
    
    async def sign_payment(
        self,
        challenge: PaymentChallenge,
        user_id: str
    ) -> Optional[str]:
        """Sign payment via Privy (embedded wallet)"""
        # This would typically use Privy's embedded wallet signing API
        # For now, return None as this requires Privy SDK integration
        return None
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

