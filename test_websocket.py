#!/usr/bin/env python3
"""WebSocket接続テスト"""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/intents"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected!")
            
            # Ping送信
            await websocket.send(json.dumps({"type": "ping"}))
            print("📤 Sent: ping")
            
            # Pong受信
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)
            print(f"📥 Received: {data}")
            
            if data.get("type") == "pong":
                print("✅ WebSocket test PASSED!")
                return True
            else:
                print("❌ Unexpected response")
                return False
                
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection failed with status code: {e.status_code}")
        return False
    except asyncio.TimeoutError:
        print("❌ Timeout waiting for response")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    exit(0 if result else 1)
