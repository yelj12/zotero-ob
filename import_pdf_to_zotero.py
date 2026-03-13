#!/usr/bin/env python3
"""Import a local PDF into Zotero via the local API.

Default API base: http://localhost:23119/api
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import pathlib
import sys
import uuid
from typing import Optional
from urllib import error, request


def build_multipart_form(fields: dict[str, str], file_field: str, file_path: pathlib.Path) -> tuple[bytes, str]:
    boundary = f"----ZoteroBoundary{uuid.uuid4().hex}"
    crlf = "\r\n"
    chunks: list[bytes] = []

    for key, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}{crlf}".encode(),
                f'Content-Disposition: form-data; name="{key}"{crlf}{crlf}'.encode(),
                value.encode(),
                crlf.encode(),
            ]
        )

    mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    file_data = file_path.read_bytes()
    chunks.extend(
        [
            f"--{boundary}{crlf}".encode(),
            f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"{crlf}'.encode(),
            f"Content-Type: {mime_type}{crlf}{crlf}".encode(),
            file_data,
            crlf.encode(),
            f"--{boundary}--{crlf}".encode(),
        ]
    )

    return b"".join(chunks), boundary


def import_pdf(
    pdf_path: pathlib.Path,
    api_base: str,
    api_key: Optional[str] = None,
    library_type: str = "users",
    library_id: str = "0",
) -> tuple[int, str]:
    endpoint = f"{api_base.rstrip('/')}/{library_type}/{library_id}/items"
    fields = {
        "itemType": "attachment",
        "linkMode": "imported_file",
        "title": pdf_path.stem,
        "contentType": "application/pdf",
        "filename": pdf_path.name,
    }
    body, boundary = build_multipart_form(fields, "file", pdf_path)

    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Zotero-Write-Token": "local-pdf-import",
    }
    if api_key:
        headers["Zotero-API-Key"] = api_key

    req = request.Request(endpoint, data=body, method="POST", headers=headers)

    try:
        with request.urlopen(req, timeout=30) as resp:
            payload = resp.read().decode("utf-8", errors="replace")
            return resp.status, payload
    except error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        return exc.code, payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import a local PDF to Zotero local API")
    parser.add_argument("pdf", type=pathlib.Path, help="Path to local PDF file")
    parser.add_argument("--api-base", default="http://localhost:23119/api", help="Zotero local API base URL")
    parser.add_argument("--api-key", default=None, help="Optional Zotero API key")
    parser.add_argument("--library-type", default="users", choices=["users", "groups"])
    parser.add_argument("--library-id", default="0", help="Library ID (default: 0)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pdf_path = args.pdf.expanduser().resolve()

    if not pdf_path.exists() or not pdf_path.is_file():
        print(f"ERROR: PDF file not found: {pdf_path}", file=sys.stderr)
        return 2
    if pdf_path.suffix.lower() != ".pdf":
        print(f"ERROR: Not a PDF file: {pdf_path}", file=sys.stderr)
        return 2

    try:
        status, payload = import_pdf(
            pdf_path=pdf_path,
            api_base=args.api_base,
            api_key=args.api_key,
            library_type=args.library_type,
            library_id=args.library_id,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Request failed: {exc}", file=sys.stderr)
        return 1

    if 200 <= status < 300:
        print("Import succeeded")
        if payload:
            try:
                print(json.dumps(json.loads(payload), ensure_ascii=False, indent=2))
            except json.JSONDecodeError:
                print(payload)
        return 0

    print(f"Import failed: HTTP {status}", file=sys.stderr)
    if payload:
        print(payload, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
