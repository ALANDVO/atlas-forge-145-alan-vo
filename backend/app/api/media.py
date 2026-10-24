from fastapi import APIRouter, Request, Response, HTTPException, Header
from fastapi.responses import StreamingResponse
from pathlib import Path
import os

from app.core.config import settings

router = APIRouter(tags=["media"])

# Media directory - in production this would be configured
MEDIA_ROOT = Path("./data/media")
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

PIECE_SIZE = settings.media_range_piece_bytes


def parse_range_header(range_header: str, file_size: int) -> tuple[int, int] | None:
    """Parse Range header and return (start, end) inclusive."""
    if not range_header.startswith("bytes="):
        return None
    
    range_spec = range_header[6:]
    if "," in range_spec:
        # Multiple ranges not supported
        return None
    
    if range_spec.startswith("-"):
        # Suffix range: -N means last N bytes
        try:
            suffix = int(range_spec[1:])
            start = max(0, file_size - suffix)
            end = file_size - 1
            return (start, end)
        except ValueError:
            return None
    elif range_spec.endswith("-"):
        # Open-ended range: N- means from N to end (capped at PIECE_SIZE)
        try:
            start = int(range_spec[:-1])
            if start >= file_size:
                return None
            end = min(file_size - 1, start + PIECE_SIZE - 1)
            return (start, end)
        except ValueError:
            return None
    else:
        # Bounded range: N-M
        try:
            start_str, end_str = range_spec.split("-")
            start = int(start_str)
            end = int(end_str)
            if start > end or start >= file_size:
                return None
            end = min(end, file_size - 1)
            return (start, end)
        except ValueError:
            return None


@router.get("/{path:path}")
async def serve_media(
    path: str,
    request: Request,
    range_header: str | None = Header(None, alias="Range"),
):
    """Serve media files with bounded range support."""
    file_path = MEDIA_ROOT / path
    
    # Security: prevent directory traversal
    try:
        file_path.resolve().relative_to(MEDIA_ROOT.resolve())
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")
    
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    
    file_size = file_path.stat().st_size
    
    if range_header is None:
        # Full file request
        return StreamingResponse(
            open(file_path, "rb"),
            media_type="video/mp4",
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
            }
        )
    
    range_result = parse_range_header(range_header, file_size)
    if range_result is None:
        raise HTTPException(status_code=416, detail="Range Not Satisfiable")
    
    start, end = range_result
    content_length = end - start + 1
    
    def file_iterator():
        with open(file_path, "rb") as f:
            f.seek(start)
            remaining = content_length
            chunk_size = 64 * 1024
            while remaining > 0:
                read_size = min(chunk_size, remaining)
                chunk = f.read(read_size)
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk
    
    return StreamingResponse(
        file_iterator(),
        status_code=206,
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Content-Length": str(content_length),
        }
    )
