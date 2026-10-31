#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PLC 项目配置向导 · 本地服务
静态页面 + /api/ocr：本地图片 OCR（Windows.Media.Ocr，离线）。
仅绑定 127.0.0.1。不含任何 AI 跳转功能。
"""
import base64
import http.server
import json
import os
import socketserver
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
OCR_PS1 = os.path.join(ROOT, 'ocr.ps1')
PORT = 8787


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_POST(self):
        if self.path != '/api/ocr':
            self.send_error(404)
            return
        n = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(n)
        if not data:
            self.send_error(400)
            return
        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tmp.write(data)
        tmp.close()
        pre = None
        text, ok = '', False
        try:
            # 预处理：放大 3 倍 + 灰度（小字表格识别率显著提升）
            img_path = tmp.name
            try:
                from PIL import Image, ImageOps
                im = Image.open(tmp.name).convert('L')
                im = ImageOps.autocontrast(im)
                pre = tmp.name + '.pre.png'
                im.resize((im.width * 3, im.height * 3), Image.LANCZOS).save(pre)
                img_path = pre
            except Exception:
                pass
            r = subprocess.run(
                ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                 '-File', OCR_PS1, img_path],
                capture_output=True, timeout=120,
            )
            payload = r.stdout.decode('ascii', errors='replace').strip()
            text = base64.b64decode(payload).decode('utf-8')
            ok = bool(text.strip()) and r.returncode == 0
        except Exception as e:  # noqa: BLE001
            text = 'ocr failed: %s' % e
        finally:
            for f in (tmp.name, pre):
                if f:
                    try:
                        os.unlink(f)
                    except OSError:
                        pass
        body = json.dumps({'ok': ok, 'text': text}, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


class Server(socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == '__main__':
    with Server(('127.0.0.1', PORT), Handler) as httpd:
        print('PLC Wizard serving http://127.0.0.1:%d/  (local OCR enabled)' % PORT)
        httpd.serve_forever()
