import asyncio
import logging
import httpx

from fastmcp import FastMCP
from generate_openapi import fetch_webservices, webservices_to_openapi
from settings import settings

logger = logging.getLogger(__name__)

async def create_mcp_server() -> FastMCP:
    logger.info("Initializing MCP server '%s'", settings.mcp_name)

    services = await fetch_webservices(settings.sonarqube_base_url, settings.sonarqube_token)

    openapi_spec = webservices_to_openapi(
        services,
        base_url=settings.sonarqube_base_url,
        toolsets=settings.sonarqube_toolsets,
        read_only=settings.sonarqube_read_only,
    )

    client = httpx.AsyncClient(
        base_url=settings.sonarqube_base_url,
        headers={
            "Authorization": f"Bearer {settings.sonarqube_token}",
            "accept": "application/json",
        },
    )

    mcp = FastMCP.from_openapi(
        openapi_spec=openapi_spec,
        client=client,
        name=settings.mcp_name,
    )

    logger.info("MCP server ready with %d endpoints", len(openapi_spec["paths"]))
    return mcp

sonarqube_mcp = asyncio.run(create_mcp_server())

if __name__ == "__main__":
    logger.info("Starting server on %s:%d (%s)", settings.mcp_host, settings.mcp_port, settings.mcp_transport)
    sonarqube_mcp.run(
        transport=settings.mcp_transport,
        show_banner=False,
        host=settings.mcp_host,
        port=settings.mcp_port,
    )
