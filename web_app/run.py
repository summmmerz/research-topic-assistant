#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Start the Flask demo application."""

import argparse
import os
import sys
import threading
import time
import webbrowser


def _ensure_project_root() -> None:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


def open_browser(url: str, delay: float = 1.5) -> None:
    def _open() -> None:
        time.sleep(delay)
        webbrowser.open(url)

    threading.Thread(target=_open, daemon=True).start()


def main() -> None:
    parser = argparse.ArgumentParser(description="启动智能科研选题辅助系统 Web 演示")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址，默认 127.0.0.1")
    parser.add_argument("-p", "--port", type=int, default=5000, help="监听端口，默认 5000")
    parser.add_argument("-d", "--debug", action="store_true", help="启用 Flask 调试模式")
    parser.add_argument("-o", "--open", action="store_true", help="启动后自动打开浏览器")
    parser.add_argument("--no-check", action="store_true", help="兼容旧命令，当前不执行额外检查")
    args = parser.parse_args()

    _ensure_project_root()

    url = f"http://{args.host}:{args.port}"
    print("智能科研选题辅助系统 Web 演示")
    print(f"Vue 前端: {url}/vue/")
    print(f"健康检查: {url}/api/health")
    print(f"知识图谱: {url}/vue/knowledge-graph")
    print(f"选题推荐: {url}/vue/topic-recommendation")
    print("按 Ctrl+C 停止服务")

    if args.open:
        open_browser(url)

    from web_app.app import app, socketio

    socketio.run(
        app,
        host=args.host,
        port=args.port,
        debug=args.debug,
        use_reloader=args.debug,
    )


if __name__ == "__main__":
    main()
