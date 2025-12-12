"""
Full-featured FastAPI server example using fastx402
Demonstrates real-world payment-protected endpoints
"""

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastx402 import payment_required, configure_server
from fastx402.types import PaymentConfig

# Configure CORS for frontend access
app = FastAPI(
    title="fastx402 Example Server",
    description="Example API with x402 payment-protected endpoints",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure x402 server
# In production, load from environment variables
configure_server(
    config=PaymentConfig(
        merchant_address=os.getenv("X402_MERCHANT_ADDRESS", "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"),
        chain_id=int(os.getenv("X402_CHAIN_ID", "8453")),
        currency=os.getenv("X402_CURRENCY", "USDC")
    )
)


@app.get("/")
def root():
    """Root endpoint - free access"""
    return {
        "message": "Welcome to fastx402 Example API",
        "endpoints": {
            "free": "/free - Free endpoint",
            "paid": "/paid - Paid endpoint (0.01 USDC)",
            "premium": "/premium - Premium endpoint (0.05 USDC)",
            "api": "/api/data - API data endpoint (0.02 USDC)",
            "download": "/download/{file_id} - Download endpoint (0.03 USDC)"
        }
    }


@app.get("/free")
def free_endpoint():
    """Free endpoint - no payment required"""
    return {
        "message": "This endpoint is free!",
        "data": "Public information available to everyone"
    }


@app.get("/paid")
@payment_required(
    price="0.01",
    currency="USDC",
    chain_id=8453,
    description="Basic paid endpoint access"
)
def paid_endpoint(request: Request):
    """Paid endpoint - requires 0.01 USDC payment"""
    return {
        "message": "You paid! Here's your content.",
        "data": "Premium content here",
        "access_level": "basic",
        "features": ["feature1", "feature2"]
    }


@app.get("/premium")
@payment_required(
    price="0.05",
    currency="USDC",
    chain_id=8453,
    description="Premium tier access"
)
def premium_endpoint(request: Request):
    """Premium endpoint - requires 0.05 USDC payment"""
    return {
        "message": "You paid for premium!",
        "tier": "premium",
        "features": ["feature1", "feature2", "feature3", "feature4"],
        "unlimited_access": True
    }


@app.get("/api/data")
@payment_required(
    price="0.02",
    currency="USDC",
    chain_id=8453,
    description="API data access"
)
def api_data_endpoint(request: Request):
    """API data endpoint - requires 0.02 USDC payment"""
    return {
        "message": "API data retrieved successfully",
        "data": {
            "users": 1000,
            "transactions": 5000,
            "revenue": "10000 USDC"
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }


@app.get("/download/{file_id}")
@payment_required(
    price="0.03",
    currency="USDC",
    chain_id=8453,
    description=f"File download access"
)
def download_endpoint(file_id: str, request: Request):
    """Download endpoint - requires 0.03 USDC payment"""
    return {
        "message": "Download authorized",
        "file_id": file_id,
        "download_url": f"https://example.com/files/{file_id}",
        "expires_in": 3600
    }


@app.post("/api/submit")
@payment_required(
    price="0.01",
    currency="USDC",
    chain_id=8453,
    description="Form submission fee"
)
async def submit_endpoint(request: Request):
    """POST endpoint with payment requirement"""
    body = await request.json()
    return {
        "message": "Submission received and processed",
        "submitted_data": body,
        "status": "success"
    }


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("fastx402 Example Server")
    print("="*60)
    print("\nStarting server on http://0.0.0.0:8000")
    print("\nAvailable endpoints:")
    print("  GET  /              - Root (free)")
    print("  GET  /free          - Free endpoint")
    print("  GET  /paid          - Paid endpoint (0.01 USDC)")
    print("  GET  /premium       - Premium endpoint (0.05 USDC)")
    print("  GET  /api/data      - API data (0.02 USDC)")
    print("  GET  /download/{id} - Download (0.03 USDC)")
    print("  POST /api/submit    - Submit (0.01 USDC)")
    print("\n" + "="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8001)

