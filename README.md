# fastx402

FastAPI integration for [x402](https://x402.io) HTTP-native payments using stablecoins. This library enables Python backend servers to protect API endpoints with payment requirements using HTTP 402 responses and EIP-712 signature verification.

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

## Core Architecture

### Server-Side Components

**`X402Server`** - Core server class for payment challenge management:
- Creates payment challenges with price, currency, chain ID, merchant address, and nonce
- Issues HTTP 402 Payment Required responses with challenge data
- Verifies payment signatures from `X-PAYMENT` headers
- Supports two payment modes: instant (local verification) and embedded (WAAS)

**`@payment_required` Decorator** - FastAPI route decorator:
- Checks for `X-PAYMENT` header on incoming requests
- If missing, returns HTTP 402 with payment challenge
- If present, verifies signature before executing route handler
- Supports per-route configuration (price, currency, chain ID, description)

### Client-Side Components

**`X402Client`** - Async httpx-based client:
- Automatically detects 402 responses
- Triggers payment signing flow via RPC handler
- Retries requests with signed `X-PAYMENT` headers
- Supports all HTTP methods (GET, POST, PUT, DELETE, PATCH)

**`X402Session`** - Requests library wrapper:
- Wraps `requests.Session` for synchronous HTTP requests
- Handles 402 challenges and retries with payment signatures
- Drop-in replacement for standard requests sessions

**`X402HttpxClient`** - httpx wrapper (sync/async):
- Supports both synchronous and asynchronous usage
- Automatic 402 handling with callback-based payment signing
- Context manager support for resource cleanup

## Payment Flow

The x402 payment flow follows these steps:

1. **Client Request**: Client makes HTTP request to protected endpoint
2. **402 Response**: Server responds with HTTP 402 and payment challenge JSON
3. **Challenge Display**: Client displays payment details (price, currency, merchant)
4. **User Signing**: User signs challenge using EIP-712 with their wallet
5. **Retry with Payment**: Client retries request with `X-PAYMENT` header containing signature
6. **Verification**: Server verifies signature and grants access
7. **Content Delivery**: Server returns protected content

## Features

### 1. EIP-712 Signature Support

- Uses EIP-712 structured data signing for secure payment verification
- Includes domain separator, type definitions, and message encoding
- Signature verification using `eth-account` library
- Supports checksum address validation

### 2. Payment Modes (Client-Side)

**Instant Mode** (default):
- Client uses user's wallet (MetaMask, WalletConnect, etc.) to sign payments
- Server verifies signatures cryptographically
- No external dependencies for verification

**Embedded Mode**:
- Client uses Wallet-as-a-Service (WAAS) providers like Privy for signing
- Server verifies signatures cryptographically (same as instant mode)
- WAAS provider handles wallet management on client side

**Note**: Mode is configured on the client, not the server. The server always verifies signatures the same way.

### 3. Configuration Options

**Server Environment Variables**:
- `X402_MERCHANT_ADDRESS`: Merchant wallet address (required)
- `X402_CHAIN_ID`: Default chain ID (e.g., 8453 for Base)
- `X402_CURRENCY`: Default currency (e.g., USDC)

**Per-Route Configuration**:
- Override defaults on individual endpoints
- Custom prices, currencies, chain IDs, and descriptions
- Flexible payment requirements per endpoint

### 4. Multiple HTTP Client Support

- **requests**: `X402Session` class and `patch_requests()` function
- **httpx**: `X402Client` (async) and `X402HttpxClient` (sync/async)
- Automatic 402 detection and retry logic
- Seamless integration with existing codebases

### 5. WAAS Integration (Client-Side)

- WAAS providers are configured on the client side
- Use x402instant library for client-side WAAS integration
- Privy provider implementation included in x402instant
- Easy to add support for other WAAS providers

### 6. Security Features

- **Nonce Generation**: Random nonces for replay protection
- **EIP-712 Signing**: Structured data signing prevents signature replay
- **Signature Verification**: Cryptographic verification before access
- **Address Validation**: Checksum address validation and normalization
- **Error Handling**: Comprehensive error messages and validation

## Configuration

### Environment Variables

```env
X402_MERCHANT_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
X402_CHAIN_ID=8453
X402_CURRENCY=USDC
```

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

### Runtime Configuration

```python
from fastx402 import configure_server

configure_server(
    config=PaymentConfig(
        merchant_address="0x...",
        chain_id=8453,
        currency="USDC"
    )
)
```

**Note**: WAAS providers are configured on the client side, not the server. See client-side usage below.

## Payment Modes (Client-Side)

### Instant Mode (Default)

Client uses user's wallet (MetaMask, WalletConnect, etc.) to sign payments. Server verifies signatures cryptographically.

**Use Cases**:
- Web applications with browser wallets
- Mobile apps with wallet integrations
- Desktop applications with wallet connections

### Embedded Mode

Client uses Wallet-as-a-Service (WAAS) providers like Privy for signing. Server verifies signatures cryptographically (same as instant mode).

**Use Cases**:
- Applications requiring embedded wallet solutions
- Applications without direct wallet access
- Simplified onboarding with WAAS providers

**Note**: Mode is configured on the client side using x402instant library. See x402instant documentation for WAAS setup.

## Client Usage

### Async Client (httpx)

For backend-to-backend requests that need to handle 402 challenges:

**Using WebSocket server (frontend x402instant connects to us):**
```python
from fastx402 import X402Client

# Client starts WebSocket server - frontend x402instant auto-connects
client = X402Client(
    base_url="https://api.example.com",
    ws_port=4021  # Frontend x402instant will connect to this
)

response = await client.get("/paid-endpoint")
data = await response.json()
```

**Using RPC handler (local signing):**
```python
from fastx402 import X402Client
from fastx402.types import PaymentChallenge, PaymentSignature

async def sign_payment(challenge: PaymentChallenge) -> Optional[PaymentSignature]:
    # Sign challenge locally (e.g., using private key or WAAS)
    return signed_payment

client = X402Client(
    base_url="https://api.example.com",
    rpc_handler=sign_payment
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

## Framework Wrappers

fastx402 provides convenience wrappers for popular frameworks to enable x402 payment handling:

### FastAPI Server Wrapper

Enable FastAPI servers to make outgoing x402 requests to other services:

```python
from fastapi import FastAPI
from fastx402 import wrap_fastapi_server

app = FastAPI()

async def handle_x402(challenge):
    return await sign_payment(challenge)

# Wrap the FastAPI app to enable x402 requests
app = wrap_fastapi_server(
    app=app,
    handle_x402=handle_x402
)

@app.get("/proxy")
async def proxy_endpoint():
    # Use the x402-enabled client from app state
    client = app.state.x402_client
    response = await client.get("https://api.example.com/paid-endpoint")
    return await response.json()
```

Or use the `X402FastAPIApp` class:

```python
from fastx402 import X402FastAPIApp

async def handle_x402(challenge):
    return await sign_payment(challenge)

app = X402FastAPIApp(
    handle_x402=handle_x402
)

@app.app.get("/proxy")
async def proxy_endpoint():
    client = app.app.state.x402_client
    response = await client.get("https://api.example.com/paid")
    return await response.json()
```

### FastMCP Client Wrapper

Wrap FastMCP clients to automatically catch 402 responses and fire callbacks:

```python
from fastmcp import Client as FastMCPClient
from fastx402 import wrap_fastmcp_client

async def handle_x402(challenge):
    return await sign_payment(challenge)

# Wrap existing FastMCP client
mcp_client = FastMCPClient("https://api.example.com/mcp")
wrapped_client = wrap_fastmcp_client(
    handle_x402=handle_x402,
    mcp_client=mcp_client
)

async with wrapped_client as client:
    result = await client.call_tool("tool_name", {"param": "value"})
```

Or use the `X402FastMCPClient` class:

```python
from fastx402 import X402FastMCPClient

async def handle_x402(challenge):
    return await sign_payment(challenge)

client = X402FastMCPClient(
    url="https://api.example.com/mcp",
    handle_x402=handle_x402
)

async with client as mcp:
    result = await mcp.call_tool("tool_name", {"param": "value"})
```

### FastMCP Server Wrapper

Enable FastMCP servers to make outgoing x402 requests to other services:

```python
from fastmcp import Server as FastMCPServer
from fastx402 import wrap_fastmcp_server

async def handle_x402(challenge):
    return await sign_payment(challenge)

# Wrap existing FastMCP server
server = FastMCPServer()
wrapped_server = wrap_fastmcp_server(
    handle_x402=handle_x402,
    mcp_server=server
)

# Now server can make x402 requests
response = await wrapped_server.x402_client.get("https://api.example.com/paid")
```

Or use the `X402FastMCPServer` class:

```python
from fastx402 import X402FastMCPServer

async def handle_x402(challenge):
    return await sign_payment(challenge)

server = X402FastMCPServer(
    handle_x402=handle_x402
)

# Make x402 requests using the attached client
response = await server.x402_client.get("https://api.example.com/paid")
```

**Note**: FastMCP wrappers require `fastmcp` to be installed. FastAPI server wrapper requires `fastapi` to be installed. These are optional dependencies and the wrappers will only be available if the respective packages are installed.

## Type System

The library uses Pydantic models for type safety and validation:

- **`PaymentChallenge`**: Payment challenge structure with price, currency, chain ID, merchant, timestamp, description, and nonce
- **`PaymentConfig`**: Global payment configuration
- **`PaymentVerificationResult`**: Result of payment signature verification
- **`PaymentSignature`**: Signed payment payload with signature, signer, and challenge

## API Reference

### Server Functions

- `payment_required(price, currency=None, chain_id=None, description=None)` - FastAPI decorator for payment protection
- `configure_server(config=None)` - Configure global server instance
- `X402Server` - Server class for challenge creation and verification
  - `create_challenge(price, currency=None, chain_id=None, description=None)` - Create payment challenge
  - `verify_payment_header(request)` - Verify X-PAYMENT header
  - `issue_402_response(challenge)` - Create HTTP 402 response

### Client Classes

- `X402Client` - Async httpx client
  - `get(path, **kwargs)` - GET request
  - `post(path, **kwargs)` - POST request
  - `request(method, path, **kwargs)` - Generic request
- `X402Session` - Requests session wrapper
- `X402HttpxClient` - httpx wrapper (sync/async)
- `patch_requests(handle_x402, session=None)` - Patch requests session

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

## Dependencies

- `fastapi>=0.104.0` - Web framework
- `httpx>=0.25.0` - Async HTTP client
- `requests>=2.31.0` - Synchronous HTTP client
- `python-dotenv>=1.0.0` - Environment variable management
- `pydantic>=2.0.0` - Data validation
- `eth-account>=0.9.0` - Ethereum account and signing
- `eth-utils>=2.0.0` - Ethereum utilities

## Testing

```bash
pytest
```

## Examples

See the `example/` directory for complete working examples:
- Server with multiple payment-protected endpoints
- CLI client that handles 402 challenges and signs payments
- Integration examples with different payment scenarios

## License

MIT
