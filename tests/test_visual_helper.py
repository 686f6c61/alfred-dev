#!/usr/bin/env python3
"""Tests de unidad ligeros para visual/scripts/helper.js."""

import json
import os
import subprocess
import textwrap
import unittest


HELPER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "visual",
    "scripts",
    "helper.js",
)


class TestVisualHelper(unittest.TestCase):
    def _run_helper_script(self, scenario):
        script = textwrap.dedent(
            """
            const fs = require('node:fs');
            const vm = require('node:vm');

            const helperPath = process.argv[1];
            const scenario = process.argv[2];
            const code = fs.readFileSync(helperPath, 'utf8');

            const connectionDot = { style: {} };
            const indicator = { textContent: '', style: {} };
            const clickHandlers = {};

            class FakeWebSocket {
              constructor(url) {
                this.url = url;
                this.sent = [];
                this.readyState = FakeWebSocket.CONNECTING;
                FakeWebSocket.instances.push(this);
              }

              send(data) {
                this.sent.push(JSON.parse(data));
              }

              emitOpen() {
                this.readyState = FakeWebSocket.OPEN;
                if (this.onopen) this.onopen();
              }
            }

            FakeWebSocket.instances = [];
            FakeWebSocket.CONNECTING = 0;
            FakeWebSocket.OPEN = 1;
            FakeWebSocket.CLOSING = 2;
            FakeWebSocket.CLOSED = 3;

            const document = {
              addEventListener(type, handler) {
                clickHandlers[type] = handler;
              },
              getElementById(id) {
                if (id === 'alfred-connection-dot') return connectionDot;
                if (id === 'alfred-indicator') return indicator;
                return null;
              },
            };

            const window = {
              location: { host: 'localhost:7331', protocol: 'http:' },
              setTimeout,
              clearTimeout,
            };

            global.window = window;
            global.document = document;
            global.WebSocket = FakeWebSocket;
            global.setTimeout = setTimeout;
            global.clearTimeout = clearTimeout;

            vm.runInThisContext(code, { filename: helperPath });

            const socket = FakeWebSocket.instances[0];

            function buildChoiceElement(choice, label, headingTag) {
              const sibling = {
                classList: {
                  remove() {},
                },
              };

              return {
                parentElement: {
                  querySelectorAll() {
                    return [sibling];
                  },
                },
                classList: {
                  add() {},
                  remove() {},
                },
                getAttribute(name) {
                  return name === 'data-choice' ? choice : null;
                },
                querySelector(selector) {
                  if (selector.indexOf(headingTag) !== -1) {
                    return { textContent: label };
                  }
                  return null;
                },
              };
            }

            if (scenario === 'queued-choice') {
              window.alfred.choice('A', 'Alpha');
              const beforeOpen = socket.sent.length;
              socket.emitOpen();
              console.log(JSON.stringify({
                url: socket.url,
                beforeOpen,
                afterOpen: socket.sent.length,
                firstMessage: socket.sent[0],
                connectionColor: connectionDot.style.background,
              }));
              process.exit(0);
            }

            if (scenario === 'heading-label') {
              socket.emitOpen();
              const element = buildChoiceElement('B', 'Editorial cálido', 'h2');
              window.toggleSelect(element);
              console.log(JSON.stringify({
                selectedChoice: window.selectedChoice,
                message: socket.sent[0],
                indicator: indicator.textContent,
              }));
              process.exit(0);
            }

            process.exit(2);
            """
        )

        result = subprocess.run(
            ["node", "-e", script, HELPER_PATH, scenario],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        return json.loads(result.stdout)

    def test_choice_is_queued_until_websocket_opens(self):
        payload = self._run_helper_script("queued-choice")
        self.assertEqual(payload["url"], "ws://localhost:7331")
        self.assertEqual(payload["beforeOpen"], 0)
        self.assertEqual(payload["afterOpen"], 1)
        self.assertEqual(payload["firstMessage"]["choice"], "A")
        self.assertEqual(payload["firstMessage"]["label"], "Alpha")
        self.assertEqual(payload["connectionColor"], "#27ae60")

    def test_toggle_select_uses_heading_label_beyond_h3(self):
        payload = self._run_helper_script("heading-label")
        self.assertEqual(payload["selectedChoice"], "B")
        self.assertEqual(payload["message"]["choice"], "B")
        self.assertEqual(payload["message"]["label"], "Editorial cálido")
        self.assertIn("Editorial cálido", payload["indicator"])


if __name__ == "__main__":
    unittest.main()
