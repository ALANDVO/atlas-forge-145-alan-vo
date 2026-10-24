import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "atlas-forge-145-alan-vo"
        assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_media_endpoint_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/media/nonexistent.mp4")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_media_range_parsing():
    from app.api.media import parse_range_header
    
    # Test bounded range
    assert parse_range_header("bytes=0-100", 1000) == (0, 100)
    
    # Test open-ended range (capped at PIECE_SIZE = 4MB)
    # Default PIECE_SIZE is 4MB, so start + 4MB - 1
    result = parse_range_header("bytes=100-", 10000)
    assert result is not None
    start, end = result
    assert start == 100
    # Should be capped at PIECE_SIZE (4MB) but file is only 10000 bytes
    assert end == 9999  # file_size - 1
    
    # Test suffix range
    assert parse_range_header("bytes=-500", 1000) == (500, 999)
    
    # Test invalid ranges
    assert parse_range_header("bytes=2000-", 1000) is None  # start beyond file
    assert parse_range_header("bytes=500-400", 1000) is None  # start > end
    assert parse_range_header("bytes=abc-", 1000) is None  # invalid format


@pytest.mark.asyncio
async def test_media_open_ended_range_capped():
    """Test that open-ended ranges are capped at PIECE_SIZE."""
    from app.api.media import parse_range_header
    from app.core.config import settings
    
    piece_size = settings.media_range_piece_bytes
    file_size = piece_size * 10  # 10x the piece size
    
    # Open-ended range from start
    result = parse_range_header("bytes=0-", file_size)
    assert result is not None
    start, end = result
    assert start == 0
    assert end == piece_size - 1  # Capped at PIECE_SIZE
    
    # Open-ended range from middle
    result = parse_range_header(f"bytes={piece_size * 2}-", file_size)
    assert result is not None
    start, end = result
    assert start == piece_size * 2
    assert end == piece_size * 3 - 1  # Capped at PIECE_SIZE from start
