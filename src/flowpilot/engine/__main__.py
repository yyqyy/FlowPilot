from __future__ import annotations

import threading
import webbrowser

import uvicorn

from flowpilot.engine.server import build_runtime, create_app

HOST = "127.0.0.1"
PORT = 8765


def main() -> int:
    runtime = build_runtime()
    app = create_app(runtime)
    if not runtime.binder.available:
        print("提示：全局快捷键不可用（可能缺少 keyboard 库或权限），仍可在界面里手动运行。")

    url = f"http://{HOST}:{PORT}/"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    print(f"FlowPilot 引擎已启动：{url}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
