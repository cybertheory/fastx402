# fastx402

FastAPI integration for [x402](https://x402.io) HTTP-native payments using stablecoins.

## Related Packages

- **[fastx402-ts](https://github.com/cybertheory/fastx402-ts)** - TypeScript/Express version for Node.js backends
- **[x402instant](https://github.com/cybertheory/x402instant)** - Frontend SDK for browser-based wallet integration

## Installation

```bash
pip install fastx402
```

## Quick Start

### 1. Environment Setup

Create a `.env` file:

```env
X402_MERCHANT_ADDRESS=0xYourMerchantAddress
X402_CHAIN_ID=8453
X402_CURRENCY=USDC
X402_MODE=instant
```

### 2. Basic Usage

```python
from fastapi import FastAPI
from fastx402 import payment_required

app = FastAPI()

@app.get("/free")
def free_route():
    return {"msg": "no charge"}

@app.get("/paid")
@payment_required(price="0.01", currency="USDC", chain_id="8453")
def paid_route():
    return {"msg": "you paid!"}
```

### 3. Run Server

```bash
uvicorn main:app --reload
```

## Configuration

### Environment Variables

- `X402_MERCHANT_ADDRESS`: Your merchant wallet address (required)
- `X402_CHAIN_ID`: Default chain ID (e.g., `8453` for Base)
- `X402_CURRENCY`: Default currency (e.g., `USDC`)
- `X402_MODE`: Payment mode - `instant` (frontend RPC) or `embedded` (WAAS)

### Per-Route Configuration

```python
@app.get("/expensive")
@payment_required(
    price="0.05",
    currency="USDC",
    chain_id="8453",
    description="Premium content access"
)
def expensive_route():
    return {"content": "premium data"}
```

## Payment Modes

### Instant Mode (Default)

Frontend handles wallet signing via RPC. The server verifies signatures.

### Embedded Mode

Uses Wallet-as-a-Service (WAAS) providers like Privy for embedded wallet signing.

## WAAS Integration

### Privy Setup

```python
from fastx402.waas import PrivyProvider

# Configure Privy in your app initialization
privy = PrivyProvider(
    app_id="your-privy-app-id",
    app_secret="your-privy-app-secret"
)
```

## Client Usage

### Async Client (httpx)

For backend-to-backend requests that need to handle 402 challenges:

```python
from fastx402 import X402Client

client = X402Client(
    base_url="https://api.example.com",
    wallet_provider="instant"  # or "embedded"
)

response = await client.get("/paid-endpoint")
data = await response.json()
```

### Requests Wrapper

Wrap `requests` library to automatically handle 402 challenges:

```python
from fastx402 import patch_requests

def handle_x402(challenge):
    # Sign challenge and return X-PAYMENT header value
    return signed_payment_header

session = patch_requests(handle_x402=handle_x402)
response = session.get("https://api.example.com/protected")
data = response.json()
```

Or use the `X402Session` class:

```python
from fastx402 import X402Session

def handle_x402(challenge):
    return signed_payment_header

session = X402Session(handle_x402=handle_x402)
response = session.get("https://api.example.com/protected")
```

### httpx Wrapper

Wrap `httpx` for async requests:

```python
from fastx402 import X402HttpxClient

async def handle_x402(challenge):
    return await sign_payment(challenge)

# Sync usage
client = X402HttpxClient(handle_x402=handle_x402)
response = client.get("https://api.example.com/protected")

# Async usage
async def main():
    async with X402HttpxClient(handle_x402=handle_x402) as client:
        response = await client.get("https://api.example.com/protected")
```

## Frontend Integration

For frontend applications, use **[x402instant](https://github.com/cybertheory/x402instant)** to handle wallet connections and payment signing:

```python
# Backend (fastx402)
@app.get("/paid")
@payment_required(price="0.01", currency="USDC", chain_id="8453")
def paid_route():
    return {"msg": "you paid!"}
```

```typescript
// Frontend (x402instant)
import { x402Fetch } from "x402instant";

const response = await x402Fetch("http://api.example.com/paid");
const data = await response.json();
```

## Testing

```bash
pytest
```

## License

MIT

# fastx402
