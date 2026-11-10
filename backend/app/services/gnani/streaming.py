"""
Gnani Prisma v3.0 Real-time WebSocket Streaming Relay.
Official Gnani Endpoint: wss://api.vachana.ai/stt/v3/stream

Architecture:
Browser (Client) <--- WebSocket ---> VAANI FastAPI Backend <--- WebSocket ---> Gnani STT (api.vachana.ai)
- Secure backend mediation: Keeps GNANI_API_KEY safe on server.
- Audio format: 16 kHz Mono, Signed 16-bit little-endian PCM, 1,024-byte frames.
- Connection headers: x-api-key-id, language_code, model=prisma-v3.0, format=transcribe.
"""

import asyncio
import json
from typing import Optional, Dict, Any
try:
    import websockets
    from websockets.exceptions import InvalidStatusCode
except ImportError:
    websockets = None
    InvalidStatusCode = Exception
from fastapi import WebSocket, WebSocketDisconnect

from app.services.gnani.config import GnaniConfig

class GnaniStreamingRelay:
    """Manages real-time bidirectional audio streaming between browser and Gnani WebSocket."""

    @classmethod
    async def handle_client_stream(
        cls,
        client_ws: WebSocket,
        language_code: Optional[str] = "indic-auto"
    ):
        """
        Accepts browser client WebSocket and pipes PCM frames to Gnani while
        piping transcript events back to the client.
        """
        await client_ws.accept()

        if websockets is None:
            await client_ws.send_text(json.dumps({
                "type": "error",
                "message": "Real-time WebSocket streaming relay is unavailable (websockets library not loaded)."
            }))
            await client_ws.close()
            return

        if not GnaniConfig.is_configured():
            await client_ws.send_json({
                "type": "error",
                "error_code": "CONFIGURATION_MISSING",
                "message": "Gnani API key is not configured in .env. Real-time streaming unavailable."
            })
            await client_ws.close()
            return

        endpoint = GnaniConfig.get_ws_asr_endpoint()
        lang = language_code if language_code and language_code != "auto" else "indic-auto"
        headers = {
            "x-api-key-id": GnaniConfig.get_api_key(),
            "language_code": lang,
            "model": "prisma-v3.0",
            "format": "transcribe"
        }

        try:
            async with websockets.connect(
                endpoint,
                additional_headers=headers,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5
            ) as gnani_ws:
                # Notify client that stream is open and ready
                await client_ws.send_json({
                    "type": "ready",
                    "model": "prisma-v3.0",
                    "language_code": lang,
                    "frame_size": 1024,
                    "sample_rate": 16000
                })

                async def pump_client_to_gnani():
                    """Read PCM audio from client and stream to Gnani."""
                    try:
                        while True:
                            message = await client_ws.receive()
                            if "bytes" in message and message["bytes"]:
                                data = message["bytes"]
                                # Stream 1,024-byte chunks to Gnani
                                chunk_size = 1024
                                for i in range(0, len(data), chunk_size):
                                    chunk = data[i:i + chunk_size]
                                    await gnani_ws.send(chunk)
                            elif "text" in message and message["text"]:
                                try:
                                    ctrl = json.loads(message["text"])
                                    # Support control frame (e.g. stop or ping)
                                    if ctrl.get("type") == "stop":
                                        break
                                except Exception:
                                    pass
                    except WebSocketDisconnect:
                        pass
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        print(f"[Streaming Relay] Client-to-Gnani pump error: {e}")

                async def pump_gnani_to_client():
                    """Read transcript and VAD events from Gnani and forward to client."""
                    try:
                        async for msg in gnani_ws:
                            if isinstance(msg, str):
                                try:
                                    payload = json.loads(msg)
                                    await client_ws.send_json(payload)
                                except Exception:
                                    await client_ws.send_text(msg)
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        print(f"[Streaming Relay] Gnani-to-Client pump error: {e}")

                client_task = asyncio.create_task(pump_client_to_gnani())
                gnani_task = asyncio.create_task(pump_gnani_to_client())

                # Wait until one terminates, then cancel the other
                done, pending = await asyncio.wait(
                    [client_task, gnani_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                for task in pending:
                    task.cancel()

        except websockets.exceptions.InvalidStatusCode as e:
            await client_ws.send_json({
                "type": "error",
                "error_code": "AUTH_FAILED" if e.status_code == 401 else "UPSTREAM_ERROR",
                "message": f"Gnani WebSocket rejected connection with status {e.status_code}."
            })
            await client_ws.close()
        except Exception as e:
            try:
                await client_ws.send_json({
                    "type": "error",
                    "error_code": "CONNECTION_FAILED",
                    "message": f"Could not connect to Gnani real-time stream: {str(e)}"
                })
                await client_ws.close()
            except Exception:
                pass

