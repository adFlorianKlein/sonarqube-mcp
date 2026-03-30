import logging
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    sonarqube_base_url: str = os.environ["SONARQUBE_BASE_URL"]
    sonarqube_token: str = os.environ["SONARQUBE_TOKEN"]
    sonarqube_toolsets: list[str] | None = (
        [t.strip() for t in os.environ["SONARQUBE_TOOLSETS"].split(",") if t.strip()]
        if os.environ.get("SONARQUBE_TOOLSETS")
        else None
    )
    sonarqube_read_only: bool = os.environ.get("SONARQUBE_READ_ONLY", "false").lower() == "true"
    output_file: str = os.environ.get("OUTPUT_FILE", "sonarqube_openapi.json")
    mcp_name: str = os.environ.get("MCP_NAME", "sonarqube-mcp")
    mcp_host: str = os.environ.get("MCP_HOST", "127.0.0.1")
    mcp_port: int = int(os.environ.get("MCP_PORT", "8070"))
    mcp_transport: str = os.environ.get("MCP_TRANSPORT", "http")
    log_level: str = os.environ.get("LOG_LEVEL", "INFO").upper()


settings = Settings()

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
