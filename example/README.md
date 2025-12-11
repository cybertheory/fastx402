# fastx402 Example

Full-featured example demonstrating x402 payment-protected API endpoints with a CLI client.

## Features

- **Server**: FastAPI server with multiple payment-protected endpoints
- **Client**: CLI client that handles 402 challenges, signs payments, and retries requests

## Setup

### 1. Install Dependencies

```bash
cd fastx402
pip install -e .
pip install uvicorn httpx eth-account python-dotenv
```

### 2. Configure Environment (Optional)

Create a `.env` file or set environment variables:

```bash
export X402_MERCHANT_ADDRESS="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
export X402_CHAIN_ID="8453"
export X402_CURRENCY="USDC"
```

For the client, set your private key (for testing only):

```bash
export PRIVATE_KEY="your_private_key_here"
```

⚠️ **Warning**: Never commit private keys to version control!

## Running the Server

```bash
cd example
python server.py
```

The server will start on `http://localhost:8000`

### Available Endpoints

- `GET /` - Root endpoint (free)
- `GET /free` - Free endpoint
- `GET /paid` - Paid endpoint (0.01 USDC)
- `GET /premium` - Premium endpoint (0.05 USDC)
- `GET /api/data` - API data endpoint (0.02 USDC)
- `GET /download/{file_id}` - Download endpoint (0.03 USDC)
- `POST /api/submit` - Submit endpoint (0.01 USDC)

## Running the CLI Client

### Basic Usage

```bash
# Make a free request
python client_cli.py get /free

# Make a paid request (will prompt for payment signature)
python client_cli.py get /paid

# Make a POST request
python client_cli.py post /api/submit --data '{"name": "test", "value": 123}'

# Use custom server URL
python client_cli.py get /paid --url http://localhost:8000

# Use custom private key
python client_cli.py get /paid --key 0x1234...
```

### Example Session

```bash
$ python client_cli.py get /free

🚀 fastx402 CLI Client
============================================================

🔄 Making GET request to /free...
Status: 200
✅ Success!
{
  "message": "This endpoint is free!",
  "data": "Public information available to everyone"
}

$ python client_cli.py get /paid

🚀 fastx402 CLI Client
============================================================

🔄 Making GET request to /paid...
Status: 402
============================================================
💰 Payment Required
============================================================
Price:     0.01 USDC
Chain ID:  8453
Merchant:  0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
Description: Basic paid endpoint access

Signing address: 0xYourAddress...

Signing payment challenge...
✅ Payment signed successfully!
============================================================

🔄 Retrying request with payment signature...
Status: 200
✅ Success!
{
  "message": "You paid! Here's your content.",
  "data": "Premium content here",
  "access_level": "basic",
  "features": ["feature1", "feature2"]
}
```

## How It Works

1. **Client makes request** to a payment-protected endpoint
2. **Server responds with 402** Payment Required and a challenge
3. **Client receives challenge** and displays payment details
4. **Client signs challenge** using EIP-712 with wallet private key
5. **Client retries request** with `X-PAYMENT` header containing signature
6. **Server verifies signature** and returns protected content

## Testing

You can test the flow using curl:

```bash
# Free endpoint (no payment)
curl http://localhost:8000/free

# Paid endpoint (will get 402)
curl http://localhost:8000/paid

# With payment header (after signing)
curl -H "X-PAYMENT: {...}" http://localhost:8000/paid
```

## Security Notes

- This example uses a private key directly for signing (testing only)
- In production, use a secure wallet provider or hardware wallet
- Never expose private keys in client-side code
- Use environment variables for sensitive configuration
- Consider using WAAS (Wallet as a Service) for embedded mode

## Next Steps

- Integrate with a real wallet provider (MetaMask, WalletConnect, etc.)
- Add payment verification on-chain
- Implement payment caching/nonce tracking
- Add rate limiting and abuse prevention
