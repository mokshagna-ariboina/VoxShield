import asyncio
import websockets
import json

connected_clients = {}

async def handler(websocket): # removed 'path' as it's deprecated in new websockets version when not needed
    client_id = None
    try:
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get('type')

            if msg_type == 'register':
                client_id = data.get('id')
                connected_clients[client_id] = websocket
                print(f"Registered client: {client_id}")
            elif msg_type in ['offer', 'answer', 'ice_candidate']:
                target = data.get('target')
                if target in connected_clients:
                    await connected_clients[target].send(json.dumps({
                        'type': msg_type,
                        'sender': client_id,
                        'payload': data.get('payload')
                    }))
                    print(f"Routed {msg_type} from {client_id} to {target}")
                else:
                    print(f"Target {target} not found for {msg_type} from {client_id}")
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if client_id in connected_clients:
            del connected_clients[client_id]
            print(f"Unregistered client: {client_id}")

async def main():
    print("Starting VoxShield VoIP Signaling Server on ws://0.0.0.0:8765")
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
