"""
Windows 啟動入口 — 必須在 uvicorn 建立 event loop 之前設定 ProactorEventLoop，
直接在 app.main 裡設定 policy 會太晚。
"""
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
