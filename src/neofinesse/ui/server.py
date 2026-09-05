"""
neofinesse.ui.server
Lightweight zero-dependency HTTP server delivering the Phase 8 Demo & Audit UI
and REST endpoints for live and frozen benchmark investigation data.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import sys
from typing import Optional
import urllib.parse
import webbrowser

from neofinesse.ui.data_exporter import export_demo_data_file, generate_ui_demo_payload

# Base directories
PACKAGE_ROOT = Path(__file__).parent
TEMPLATES_DIR = PACKAGE_ROOT / "templates"
STATIC_DIR = PACKAGE_ROOT / "static"
DATA_FILE = PACKAGE_ROOT / "data" / "benchmark_demo_data.json"


class NeoFinesseUIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for static files and REST API endpoints."""

    def log_message(self, format: str, *args: Any) -> None:
        """Quiet logging for clean terminal output."""
        pass

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # 1. Root / UI HTML
        if path in ("/", "/index.html"):
            index_path = TEMPLATES_DIR / "index.html"
            if index_path.exists():
                content = index_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(content)
                return
            else:
                self.send_error(404, "index.html template not found")
                return

        # 2. API Endpoints
        if path == "/api/health":
            body = json.dumps({"status": "ok", "service": "neofinesse-ui", "version": "phase-8"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/api/data":
            if not DATA_FILE.exists():
                export_demo_data_file(DATA_FILE)
            content = DATA_FILE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(content)
            return

        if path == "/api/evidence/source-context":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            filename = query_params.get("file", [None])[0] or query_params.get("filename", [None])[0]
            sheet = query_params.get("sheet", [None])[0]
            cell = query_params.get("cell", [None])[0]
            row_str = query_params.get("row", [None])[0]
            col_str = query_params.get("column", [None])[0] or query_params.get("col", [None])[0]
            row_radius_str = query_params.get("row_radius", ["3"])[0]
            col_radius_str = query_params.get("column_radius", ["3"])[0]

            if not filename:
                body = json.dumps({"status": "ERROR", "error": "Missing required parameter 'file'"}).encode("utf-8")
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(body)
                return

            try:
                row_val = int(row_str) if row_str else None
                col_val = int(col_str) if (col_str and col_str.isdigit()) else col_str
                row_radius = int(row_radius_str) if row_radius_str else 3
                col_radius = int(col_radius_str) if col_radius_str else 3

                from neofinesse.services.evidence_context_service import EvidenceContextService
                dataset_dir = Path(__file__).parent.parent.parent.parent / "data" / "demo_dataset"
                service = EvidenceContextService(dataset_dir)

                context_data = service.get_cell_context(
                    filename=filename,
                    sheet=sheet,
                    cell=cell,
                    row=row_val,
                    column=col_val,
                    row_radius=row_radius,
                    column_radius=col_radius,
                )

                body = json.dumps(context_data).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(body)
                return
            except PermissionError as pe:
                body = json.dumps({"status": "ERROR", "error": str(pe)}).encode("utf-8")
                self.send_response(403)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(body)
                return
            except (FileNotFoundError, ValueError) as fe:
                body = json.dumps({"status": "ERROR", "error": str(fe)}).encode("utf-8")
                self.send_response(404)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(body)
                return
            except Exception as e:
                body = json.dumps({"status": "ERROR", "error": f"Internal server error: {str(e)}"}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(body)
                return

        if path == "/api/escalation/summary":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            scenario_id = query_params.get("scenario_id", [None])[0] or query_params.get("case_id", [None])[0]

            if not DATA_FILE.exists():
                export_demo_data_file(DATA_FILE)

            try:
                demo_data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
                scenarios = demo_data.get("scenarios", [])

                target_scen = None
                if scenario_id:
                    for s in scenarios:
                        if s.get("scenario_id") == scenario_id or s.get("case_id") == scenario_id:
                            target_scen = s
                            break

                if not target_scen:
                    # Fallback to first escalated scenario or first scenario
                    escalated = [s for s in scenarios if s.get("expected_outcome") == "ESCALATE"]
                    target_scen = escalated[0] if escalated else (scenarios[0] if scenarios else {})

                from neofinesse.services.escalation_summary_service import EscalationSummaryService
                handoff = EscalationSummaryService.generate_handoff_summary(target_scen)

                body = json.dumps({"status": "SUCCESS", "handoff": handoff.model_dump()}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(body)
                return
            except Exception as e:
                body = json.dumps({"status": "ERROR", "error": f"Failed to generate escalation summary: {str(e)}"}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(body)
                return

        # 3. Static Files (/static/css/styles.css, /static/js/app.js)
        if path.startswith("/static/"):
            rel_path = path[len("/static/"):]
            file_path = STATIC_DIR / rel_path
            # Prevent directory traversal
            try:
                resolved = file_path.resolve()
                if not str(resolved).startswith(str(STATIC_DIR.resolve())):
                    self.send_error(403, "Access denied")
                    return
            except Exception:
                self.send_error(400, "Invalid path")
                return

            if file_path.exists() and file_path.is_file():
                mime_type, _ = mimetypes.guess_type(str(file_path))
                if mime_type is None:
                    mime_type = "application/octet-stream"
                if file_path.suffix == ".css":
                    mime_type = "text/css"
                elif file_path.suffix == ".js":
                    mime_type = "application/javascript"

                content = file_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", f"{mime_type}; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(content)
                return

        # Not found
        self.send_error(404, f"Path not found: {path}")


def run_ui_server(
    host: str = "127.0.0.1",
    port: int = 8080,
    open_browser: bool = False,
    max_port_attempts: int = 10,
) -> tuple[ThreadingHTTPServer, int]:
    """
    Starts the NeoFinesse UI server with automatic port discovery.
    Returns (server_instance, bound_port).
    """
    # Ensure demo data file exists
    if not DATA_FILE.exists():
        export_demo_data_file(DATA_FILE)

    bound_server: Optional[ThreadingHTTPServer] = None
    active_port = port

    for attempt in range(max_port_attempts):
        try:
            active_port = port + attempt
            bound_server = ThreadingHTTPServer((host, active_port), NeoFinesseUIHandler)
            break
        except OSError:
            continue

    if bound_server is None:
        raise RuntimeError(f"Could not bind UI server on {host} across ports {port}-{port + max_port_attempts - 1}")

    url = f"http://{host}:{active_port}"
    print("\n" + "=" * 80)
    print("NEOFINESSE PHASE 8 — DEMO & AUDIT UI SERVER")
    print("=" * 80)
    print(f"UI Application URL:    {url}")
    print(f"REST API Endpoint:     {url}/api/data")
    print(f"Health Check:          {url}/api/health")
    print("Core Invariant:        AI investigates. Evidence constrains. Verification decides.")
    print("=" * 80 + "\n")

    if open_browser:
        webbrowser.open(url)

    return bound_server, active_port


def main() -> None:
    parser = argparse.ArgumentParser(description="NeoFinesse Phase 8 Demo & Audit UI Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Initial port (default: 8080)")
    parser.add_argument("--open-browser", action="store_true", help="Automatically open default browser")

    args = parser.parse_args()
    server, active_port = run_ui_server(
        host=args.host,
        port=args.port,
        open_browser=args.open_browser,
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down NeoFinesse UI Server...")
        server.server_close()


if __name__ == "__main__":
    main()
