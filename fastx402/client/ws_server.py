"""
WebSocket server for fastx402
Allows frontend x402instant clients to connect and handle payment signing requests
"""

import json
import asyncio
import uuid
from typing import Optional, Dict, Any, Callable, Awaitable
from fastx402.types import PaymentChallenge, PaymentSignature


class X402WebSocketServer:
    """
    WebSocket server for x402instant frontend clients
    
    This server runs in the backend and waits for frontend clients to connect.
    When a payment signature is needed, it sends a request to connected clients
    and waits for the signed response.
    
    Example:
        ```python
        from fastx402.client.ws_server import X402WebSocketServer
        
        async def main():
            server = X402WebSocketServer(port=4021, path="/x402/ws")
            await server.start()
            
            # Request payment signature from connected frontend
            challenge = PaymentChallenge(...)
            signature = await server.request_signature(challenge)
            
            await server.stop()
        ```
    """
    
    def __init__(
        self,
        port: int = 4021,
        path: str = "/x402/ws",
        timeout: float = 30.0
    ):
        """
        Initialize WebSocket server
        
        Args:
            port: Port to listen on
            path: WebSocket path
            timeout: Request timeout in seconds
        """
        self.port = port
        self.path = path
        self.timeout = timeout
        
        self.server = None
        self.clients: Dict[str, Any] = {}
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.running = False
    
    async def start(self) -> None:
        """Start WebSocket server"""
        try:
            import websockets
            from websockets.server import serve
        except ImportError:
            raise ImportError(
                "websockets package is required. Install with: pip install websockets"
            )
        
        async def handle_client(websocket, path):
            """Handle new client connection"""
            if path != self.path:
                await websocket.close(code=4004, reason="Invalid path")
                return
            
            client_id = str(uuid.uuid4())
            self.clients[client_id] = websocket
            
            try:
                # Send welcome message
                await websocket.send(json.dumps({
                    "type": "connected",
                    "clientId": client_id,
                    "message": "Connected to x402 WebSocket server"
                }))
                
                # Listen for messages
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self._handle_message(client_id, data)
                    except json.JSONDecodeError as e:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "error": f"Invalid JSON: {e}"
                        }))
                    except Exception as e:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "error": f"Error processing message: {e}"
                        }))
            
            except Exception as e:
                print(f"Client {client_id} error: {e}")
            finally:
                # Remove client on disconnect
                if client_id in self.clients:
                    del self.clients[client_id]
        
        self.server = await serve(handle_client, "localhost", self.port)
        self.running = True
        print(f"x402 WebSocket server running on ws://localhost:{self.port}{self.path}")
    
    async def _handle_message(self, client_id: str, message: Dict[str, Any]) -> None:
        """Handle incoming message from client"""
        msg_type = message.get("type")
        msg_id = message.get("id")
        
        if msg_type == "sign-response":
            # Handle payment signature response
            if msg_id and msg_id in self.pending_requests:
                future = self.pending_requests.pop(msg_id)
                
                if message.get("error"):
                    future.set_exception(Exception(message["error"]))
                else:
                    result = message.get("result")
                    if result:
                        # Convert dict to PaymentSignature
                        signature = PaymentSignature(**result)
                        future.set_result(signature)
                    else:
                        future.set_result(None)
        
        elif msg_type == "pong":
            # Heartbeat response
            pass
        
        elif msg_type == "error":
            # Handle error message
            if msg_id and msg_id in self.pending_requests:
                future = self.pending_requests.pop(msg_id)
                error_msg = message.get("error", "Unknown error")
                future.set_exception(Exception(error_msg))
    
    async def request_signature(
        self,
        challenge: PaymentChallenge
    ) -> Optional[PaymentSignature]:
        """
        Request payment signature from connected frontend clients
        
        Args:
            challenge: Payment challenge to sign
            
        Returns:
            PaymentSignature with signature, or None if signing fails
            
        Raises:
            ConnectionError: If no clients are connected
            TimeoutError: If request times out
        """
        if not self.clients:
            raise ConnectionError("No frontend clients connected. Start x402instant WebSocket client first.")
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Convert challenge to dict
        challenge_dict = challenge.model_dump() if hasattr(challenge, 'model_dump') else challenge.dict()
        
        # Create request message
        message = {
            "type": "sign-request",
            "id": request_id,
            "challenge": challenge_dict
        }
        
        # Create future for response
        future = asyncio.Future()
        self.pending_requests[request_id] = future
        
        try:
            # Send request to first available client
            # In production, you might want to implement client selection logic
            client_ws = next(iter(self.clients.values()))
            await client_ws.send(json.dumps(message))
            
            # Wait for response with timeout
            try:
                result = await asyncio.wait_for(future, timeout=self.timeout)
                return result
            except asyncio.TimeoutError:
                self.pending_requests.pop(request_id, None)
                raise TimeoutError(f"Payment signing request timed out after {self.timeout}s")
        
        except Exception as e:
            self.pending_requests.pop(request_id, None)
            raise
    
    async def stop(self) -> None:
        """Stop WebSocket server"""
        self.running = False
        
        # Close all client connections
        for client_id, websocket in list(self.clients.items()):
            try:
                await websocket.close()
            except Exception:
                pass
        self.clients.clear()
        
        # Cancel pending requests
        for future in self.pending_requests.values():
            if not future.done():
                future.cancel()
        self.pending_requests.clear()
        
        # Close server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
    
    def is_running(self) -> bool:
        """Check if server is running"""
        return self.running
    
    def get_client_count(self) -> int:
        """Get number of connected clients"""
        return len(self.clients)


