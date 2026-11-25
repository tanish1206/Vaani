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
import logging
from typing import Optional
try:
    import websockets
    try:
        from websockets.exceptions import InvalidStatus as InvalidStatusCode
    except ImportError:
        from websockets.exceptions import InvalidStatusCode
except ImportError:
    websockets = None
    InvalidStatusCode = Exception
from fastapi import WebSocket, WebSocketDisconnect

from app.services.gnani.config import GnaniConfig

logger = logging.getLogger(__name__)


class GnaniStreamingRelay:
    """Manages real-time bidirectional audio streaming between browser and Gnani WebSocket."""

    @classmethod
    async def handle_client_stream(
        cls,
        client_ws: WebSocket,
        language_code: Optional[str] = "indic-auto",
    ):
        """
        Accepts browser client WebSocket and pipes PCM frames to Gnani while
        piping transcript events back to the client.
        """
        await client_ws.accept()

        if websockets is None:
            await client_ws.send_text(json.dumps({
                "type": "error",
                "message": "Real-time WebSocket streaming relay is unavailable (websockets library not loaded).",
            }))
            await client_ws.close()
            return

        if not GnaniConfig.is_configured():
            await client_ws.send_json({
                "type": "error",
                "error_code": "CONFIGURATION_MISSING",
                "message": "Gnani API key is not configured in .env. Real-time streaming unavailable.",
            })
            await client_ws.close()
            return

        endpoint = GnaniConfig.get_ws_asr_endpoint()
        lang = language_code if language_code and language_code != "auto" else "indic-auto"
        headers = {
            "x-api-key-id": GnaniConfig.get_api_key(),
            "language_code": lang,
            "model": "prisma-v3.0",
            "format": "transcribe",
        }

        try:
            async with websockets.connect(
                endpoint,
                additional_headers=headers,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5,
            ) as gnani_ws:
                await client_ws.send_json({
                    "type": "ready",
                    "model": "prisma-v3.0",
                    "language_code": lang,
                    "frame_size": 1024,
                    "sample_rate": 16000,
                })

                async def pump_client_to_gnani():
                    """Read PCM audio from client and stream to Gnani."""
                    try:
                        while True:
                            message = await client_ws.receive()
                            if message.get("bytes"):
                                data = message["bytes"]
                                chunk_size = 1024
                                for i in range(0, len(data), chunk_size):
                                    await gnani_ws.send(data[i:i + chunk_size])
                            elif message.get("text"):
                                try:
                                    ctrl = json.loads(message["text"])
                                    if ctrl.get("type") == "stop":
                                        break
                                except json.JSONDecodeError:
                                    pass
                    except (WebSocketDisconnect, asyncio.CancelledError):
                        pass
                    except Exception as exc:
                        logger.warning("Streaming relay client-to-Gnani error: %s", exc)

                async def pump_gnani_to_client():
                    """Read transcript and VAD events from Gnani and forward to client."""
                    try:
                        async for msg in gnani_ws:
                            if isinstance(msg, str):
                                try:
                                    await client_ws.send_json(json.loads(msg))
                                except json.JSONDecodeError:
                                    await client_ws.send_text(msg)
                    except asyncio.CancelledError:
                        pass
                    except Exception as exc:
                        logger.warning("Streaming relay Gnani-to-client error: %s", exc)

                client_task = asyncio.create_task(pump_client_to_gnani())
                gnani_task = asyncio.create_task(pump_gnani_to_client())

                _, pending = await asyncio.wait(
                    [client_task, gnani_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
                    await asyncio.gather(task, return_exceptions=True)

        except InvalidStatusCode as exc:
            status_code = getattr(exc, "status_code", 502)
            await client_ws.send_json({
                "type": "error",
                "error_code": "AUTH_FAILED" if status_code == 401 else "UPSTREAM_ERROR",
                "message": f"Gnani WebSocket rejected connection with status {status_code}.",
            })
            await client_ws.close()
        except Exception as exc:
            try:
                await client_ws.send_json({
                    "type": "error",
                    "error_code": "CONNECTION_FAILED",
                    "message": f"Could not connect to Gnani real-time stream: {exc}",
                })
                await client_ws.close()
            except Exception:
                pass

