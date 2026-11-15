"""Local preview server for site/ that serves /services/x from services/x.html, like Cloudflare Pages does.

Run:  python tools/serve.py [port]
"""

import functools
import http.server
import pathlib
import sys

SITE = pathlib.Path(__file__).resolve().parent.parent / "site"


class PrettyURLHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        local = pathlib.Path(super().translate_path(path))
        if not local.exists() and local.with_suffix(".html").exists():
            return str(local.with_suffix(".html"))
        return str(local)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    handler = functools.partial(PrettyURLHandler, directory=str(SITE))
    http.server.ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()
