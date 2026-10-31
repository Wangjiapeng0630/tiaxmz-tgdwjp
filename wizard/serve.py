#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PLC 项目配置向导 · 本地服务
静态页面 + /api/handoff：保存 project.json 并拉起 `mimo run` 自动转 AI 执行。
仅绑定 127.0.0.1。
"""
import http.server
import json
import os
import socketserver
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.join(os.path.expanduser('~'), 'Documents', 'PLCWizard')
MIMO = os.path.join(os.path.expanduser('~'), '.mimocode', 'bin', 'mimo.exe')
PORT = 8787
PROMPT = ('按配置生成项目：读取当前目录 project.json，'
          '按 tiaxmz-tgdwjp skill 的六步流程生成 TIA 项目'
          '（先提纯控制要求并交使用者确认）。')


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_POST(self):
        if self.path != '/api/handoff':
            self.send_error(404)
            return
        length = int(self.headers.get('Content-Length', 0))
        try:
            cfg = json.loads(self.rfile.read(length))
            if not isinstance(cfg, dict):
                raise ValueError('not an object')
        except Exception:
            self.send_error(400, 'invalid json')
            return
        dry = bool(cfg.pop('__dry__', False))
        os.makedirs(WORKSPACE, exist_ok=True)
        out = os.path.join(WORKSPACE, 'project.json')
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        if dry:
            started = True
        else:
            exe = MIMO if os.path.isfile(MIMO) else 'mimo'
            try:
                subprocess.Popen(
                    [exe, 'run', PROMPT],
                    cwd=WORKSPACE,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
                started = True
            except Exception as e:  # noqa: BLE001
                started = False
                sys.stderr.write('spawn failed: %s\n' % e)
        body = json.dumps({'ok': started, 'workspace': WORKSPACE, 'config': out},
                          ensure_ascii=False).encode('utf-8')
        self.send_response(200 if started else 500)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        sys.stderr.write('[wiz] %s\n' % (fmt % args))


class Server(socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == '__main__':
    with Server(('127.0.0.1', PORT), Handler) as httpd:
        print('PLC Wizard serving http://127.0.0.1:%d/  workspace=%s' % (PORT, WORKSPACE))
        httpd.serve_forever()
