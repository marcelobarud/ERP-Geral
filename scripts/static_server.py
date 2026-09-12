"""Servidor estático mínimo para o build Vite com fallback de SPA."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class SpaRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - nome exigido pelo servidor HTTP
        requested_path = self.translate_path(self.path)
        if not Path(requested_path).is_file():
            self.path = "/index.html"
        super().do_GET()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve o build do ERP Geral")
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=4173, type=int)
    args = parser.parse_args()

    directory = args.directory.resolve()
    index_file = directory / "index.html"
    if not index_file.is_file():
        raise SystemExit(f"Build não encontrado: {index_file}")

    handler = partial(SpaRequestHandler, directory=str(directory))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"ERP Geral frontend: http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
