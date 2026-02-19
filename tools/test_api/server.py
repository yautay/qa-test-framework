import hashlib

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json

app = FastAPI()


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def catch_all(request: Request, path: str):
    body_bytes = await request.body()

    print("\n--- NOWY REQUEST ---")
    print(f"Metoda: {request.method}")
    print(f"URL: {request.url}")
    # print("Nagłówki:")
    # print(json.dumps(dict(request.headers), indent=2, ensure_ascii=False))

    if body_bytes:
        payload_hash = hashlib.sha256(body_bytes).hexdigest()
        print(f"Payload SHA256: {payload_hash}")
    else:
        print("Payload: brak (hash pominięty)")

    # if body_bytes:
    #     try:
    #         body_json = json.loads(body_bytes)
    #         print("Payload (pretty JSON):")
    #         print(json.dumps(body_json, indent=2, ensure_ascii=False))
    #     except Exception:
    #         print("Payload (raw):")
    #         print(body_bytes.decode("utf-8", errors="ignore"))
    # else:
    #     print("Payload: brak")

    return JSONResponse(content={"status": "ok"}, status_code=200)


#  uvicorn main:app --host 0.0.0.0 --port 3001
