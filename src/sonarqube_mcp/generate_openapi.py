"""
Fetches SonarQube web services from /api/webservices/list and converts them
into an OpenAPI 3.0.3 specification saved as JSON.
"""

import asyncio
import json
import logging
import re

import httpx

from models import Action, Param, WebService
from settings import settings

logger = logging.getLogger(__name__)


def strip_html(text: str | None) -> str | None:
    """Remove HTML tags from a description string."""
    if text is None:
        return None
    return re.sub(r"<[^>]+>", " ", text).strip()


def param_to_schema(param: Param) -> dict:
    """Convert a SonarQube Param to a JSON Schema property."""
    schema: dict = {"type": "string"}
    if param.description:
        schema["description"] = strip_html(param.description)
    if param.maximumLength:
        schema["maxLength"] = param.maximumLength
    if param.exampleValue:
        schema["example"] = param.exampleValue
    return schema


def action_to_operation(service: WebService, action: Action) -> dict:
    """Convert a single Action into an OpenAPI operation object."""
    operation: dict = {
        "operationId": f"{service.path.replace('/', '_')}_{action.key}",
        "responses": {
            "200": {"description": "Successful response"},
        },
    }

    summary_parts = []
    if action.description:
        summary_parts.append(strip_html(action.description))
    if action.deprecatedSince:
        operation["deprecated"] = True
        summary_parts.append(f"(deprecated since {action.deprecatedSince})")
    if summary_parts:
        operation["summary"] = " ".join(summary_parts)

    tags = [service.path]
    if service.description:
        tags = [service.description]
    operation["tags"] = tags

    public_params = [p for p in action.params if not p.internal]

    if action.post:
        if public_params:
            properties = {}
            required = []
            for param in public_params:
                properties[param.key] = param_to_schema(param)
                if param.required:
                    required.append(param.key)

            schema: dict = {"type": "object", "properties": properties}
            if required:
                schema["required"] = required

            operation["requestBody"] = {
                "required": bool(required),
                "content": {
                    "application/x-www-form-urlencoded": {"schema": schema}
                },
            }
    else:
        if public_params:
            parameters = []
            for param in public_params:
                param_obj: dict = {
                    "name": param.key,
                    "in": "query",
                    "required": param.required,
                    "schema": param_to_schema(param),
                }
                if param.description:
                    param_obj["description"] = strip_html(param.description)
                parameters.append(param_obj)
            operation["parameters"] = parameters

    return operation


def matches_toolset(service: WebService, toolsets: list[str] | None) -> bool:
    """Check if a service matches any of the configured toolsets."""
    if toolsets is None:
        return True
    service_name = service.path.rsplit("/", 1)[-1]
    return service_name in toolsets


async def fetch_webservices(base_url: str, token: str) -> list[WebService]:
    """Fetch public web services from a SonarQube instance."""
    logger.info("Fetching web services from %s", base_url)
    async with httpx.AsyncClient(
        base_url=base_url,
        headers={
            "Authorization": f"Bearer {token}",
            "accept": "application/json",
        },
    ) as client:
        response = await client.get(
            "api/webservices/list",
            params={"include_internals": "false"},
        )
        response.raise_for_status()
        raw_services = response.json().get("webServices", [])
    services = [WebService(**s) for s in raw_services]
    logger.info("Fetched %d web services", len(services))
    return services


def webservices_to_openapi(
    services: list[WebService],
    *,
    base_url: str,
    toolsets: list[str] | None = None,
    read_only: bool = False,
) -> dict:
    """Convert a list of WebService objects into an OpenAPI 3.0.3 spec dict."""
    paths: dict = {}

    for service in services:
        if not matches_toolset(service, toolsets):
            logger.debug("Skipping service %s (not in toolsets)", service.path)
            continue

        public_actions = [a for a in service.actions if not a.internal]
        if read_only:
            public_actions = [a for a in public_actions if not a.post]

        logger.debug("Service %s: %d public actions", service.path, len(public_actions))

        for action in public_actions:
            path = f"/{service.path}/{action.key}"
            method = "post" if action.post else "get"
            operation = action_to_operation(service, action)
            paths[path] = {method: operation}

    logger.info("Generated OpenAPI spec with %d endpoints", len(paths))

    openapi_spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "SonarQube Web API",
            "description": "Auto-generated OpenAPI spec from SonarQube /api/webservices/list",
            "version": "1.0.0",
        },
        "servers": [{"url": base_url}],
        "paths": paths,
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                }
            }
        },
        "security": [{"bearerAuth": []}],
    }

    return openapi_spec


async def main():
    services = await fetch_webservices(settings.sonarqube_base_url, settings.sonarqube_token)

    openapi_spec = webservices_to_openapi(
        services,
        base_url=settings.sonarqube_base_url,
        toolsets=settings.sonarqube_toolsets,
        read_only=settings.sonarqube_read_only,
    )

    with open(settings.output_file, "w", encoding="utf-8") as f:
        json.dump(openapi_spec, f, indent=2, ensure_ascii=False)

    path_count = len(openapi_spec["paths"])
    logger.info("OpenAPI spec written to %s (%d endpoints)", settings.output_file, path_count)


if __name__ == "__main__":
    asyncio.run(main())
