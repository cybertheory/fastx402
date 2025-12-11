"""
Example FastAPI application using fastx402
"""

from fastapi import FastAPI
from fastx402 import payment_required

app = FastAPI(title="fastx402 Example")

@app.get("/")
def root():
    return {"message": "Welcome to fastx402 example"}

@app.get("/free")
def free_route():
    return {"msg": "This endpoint is free!"}

@app.get("/paid")
@payment_required(price="0.01", currency="USDC", chain_id="8453", description="Example paid endpoint")
def paid_route():
    return {
        "msg": "You paid! Here's your content.",
        "data": "Premium content here"
    }

@app.get("/expensive")
@payment_required(price="0.05", currency="USDC", chain_id="8453", description="Premium tier access")
def expensive_route():
    return {
        "msg": "You paid for premium!",
        "tier": "premium",
        "features": ["feature1", "feature2", "feature3"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

