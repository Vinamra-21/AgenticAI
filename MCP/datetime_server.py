from mcp.server.fastmcp import FastMCP
from datetime import datetime, timezone

mcp = FastMCP("datetime_server")


@mcp.tool()
async def get_current_datetime() -> str:
    """Get the current date and time in UTC.

    Returns:
        The current UTC date and time as an ISO 8601 string
    """
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    mcp.run(transport="stdio")
