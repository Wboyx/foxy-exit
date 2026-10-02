"""tunnel service"""
import asyncio, os
from aiohttp import web, WSMsgType

UUID_HEX = os.environ.get("XRAY_UUID", "").replace("-", "").lower()

async def health(_):
    return web.json_response({"ok": True, "node": "foxy-de-node"})

async def vless_ws(ws):
    buf = b""
    while len(buf) < 22:
        msg = await ws.receive()
        if msg.type != WSMsgType.BINARY: return
        buf += msg.data
    if buf[0] != 0 or buf[1:17] != bytes.fromhex(UUID_HEX):
        await ws.send_bytes(b"\x00\x01"); return
    alen = buf[17]
    while len(buf) < 19 + alen + 3:
        msg = await ws.receive()
        if msg.type != WSMsgType.BINARY: return
        buf += msg.data
    off = 18 + alen
    cmd = buf[off]; off += 1
    port = int.from_bytes(buf[off:off + 2], "big"); off += 2
    atyp = buf[off]; off += 1
    if atyp == 1:
        host = ".".join(str(b) for b in buf[off:off + 4]); off += 4
    elif atyp == 2:
        ln = buf[off]; host = buf[off + 1:off + 1 + ln].decode(errors="ignore"); off += 1 + ln
    else:
        await ws.send_bytes(b"\x00\x01"); return
    if cmd != 1:
        await ws.send_bytes(b"\x00\x01"); return
    await ws.send_bytes(b"\x00\x00")            # پاسخ vless: ver=0, addonLen=0
    payload = buf[off:]
    try:
        r, w = await asyncio.wait_for(asyncio.open_connection(host, port), 8)
    except Exception:
        return
    if payload:
        w.write(payload); await w.drain()
    async def to_net():
        try:
            async for msg in ws:
                if msg.type == WSMsgType.BINARY:
                    w.write(msg.data); await w.drain()
                elif msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSING, WSMsgType.ERROR):
                    break
        except Exception: pass
        finally:
            try: w.close()
            except Exception: pass
    async def to_ws():
        try:
            while True:
                d = await r.read(65536)
                if not d: break
                await ws.send_bytes(d)
        except Exception: pass
    try:
        await asyncio.gather(to_net(), to_ws())
    except Exception: pass

async def handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    try:
        await vless_ws(ws)
    except Exception:
        pass
    return ws

app = web.Application()
app.router.add_get("/health", health)
app.router.add_get("/{tail:.*}", handler)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", "3000")))
