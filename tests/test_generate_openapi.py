import pytest
import httpx
import respx

from models import Action, Param, WebService
from generate_openapi import (
    action_to_operation,
    fetch_webservices,
    matches_toolset,
    param_to_schema,
    strip_html,
    webservices_to_openapi,
)


# -- strip_html --


class TestStripHtml:
    def test_removes_tags(self):
        assert strip_html("<p>Hello <b>world</b></p>") == "Hello  world"

    def test_returns_none_for_none(self):
        assert strip_html(None) is None

    def test_plain_text_unchanged(self):
        assert strip_html("no tags here") == "no tags here"

    def test_strips_surrounding_whitespace(self):
        assert strip_html("  <br/>text  ") == "text"

    def test_self_closing_tags(self):
        assert strip_html("line1<br/>line2") == "line1 line2"


# -- param_to_schema --


class TestParamToSchema:
    def test_minimal(self):
        p = Param(key="q")
        schema = param_to_schema(p)
        assert schema == {"type": "string"}

    def test_with_description_strips_html(self):
        p = Param(key="q", description="<b>Search</b> query")
        schema = param_to_schema(p)
        assert schema["description"] == "Search  query"

    def test_with_max_length(self):
        p = Param(key="name", maximumLength=200)
        schema = param_to_schema(p)
        assert schema["maxLength"] == 200

    def test_with_example(self):
        p = Param(key="key", exampleValue="my_project")
        schema = param_to_schema(p)
        assert schema["example"] == "my_project"

    def test_full(self):
        p = Param(
            key="key",
            description="Project key",
            maximumLength=100,
            exampleValue="proj",
        )
        schema = param_to_schema(p)
        assert schema == {
            "type": "string",
            "description": "Project key",
            "maxLength": 100,
            "example": "proj",
        }


# -- matches_toolset --


class TestMatchesToolset:
    def test_none_toolsets_matches_everything(self):
        ws = WebService(path="api/issues")
        assert matches_toolset(ws, None) is True

    def test_matching_toolset(self):
        ws = WebService(path="api/issues")
        assert matches_toolset(ws, ["issues", "rules"]) is True

    def test_non_matching_toolset(self):
        ws = WebService(path="api/issues")
        assert matches_toolset(ws, ["rules", "metrics"]) is False

    def test_uses_last_path_segment(self):
        ws = WebService(path="api/project_analyses")
        assert matches_toolset(ws, ["project_analyses"]) is True


# -- action_to_operation --


def _make_service(**kwargs) -> WebService:
    defaults = {"path": "api/issues", "description": "Issue tracking"}
    defaults.update(kwargs)
    return WebService(**defaults)


def _make_action(**kwargs) -> Action:
    defaults = {"key": "search"}
    defaults.update(kwargs)
    return Action(**defaults)


class TestActionToOperation:
    def test_basic_get(self):
        svc = _make_service()
        act = _make_action(description="Search issues")
        op = action_to_operation(svc, act)

        assert op["operationId"] == "api_issues_search"
        assert op["summary"] == "Search issues"
        assert op["tags"] == ["Issue tracking"]
        assert "200" in op["responses"]

    def test_deprecated_action(self):
        svc = _make_service()
        act = _make_action(description="Old search", deprecatedSince="7.0")
        op = action_to_operation(svc, act)

        assert op["deprecated"] is True
        assert "(deprecated since 7.0)" in op["summary"]

    def test_tags_fallback_to_path(self):
        svc = _make_service(description=None)
        act = _make_action()
        op = action_to_operation(svc, act)
        assert op["tags"] == ["api/issues"]

    def test_get_with_params(self):
        svc = _make_service()
        act = _make_action(
            params=[
                Param(key="q", description="Query", required=True),
                Param(key="page", description="Page number"),
            ]
        )
        op = action_to_operation(svc, act)

        assert len(op["parameters"]) == 2
        q_param = op["parameters"][0]
        assert q_param["name"] == "q"
        assert q_param["in"] == "query"
        assert q_param["required"] is True

    def test_get_filters_internal_params(self):
        svc = _make_service()
        act = _make_action(
            params=[
                Param(key="q", description="Query"),
                Param(key="internal_id", internal=True),
            ]
        )
        op = action_to_operation(svc, act)

        assert len(op["parameters"]) == 1
        assert op["parameters"][0]["name"] == "q"

    def test_post_with_params(self):
        svc = _make_service()
        act = _make_action(
            key="create",
            post=True,
            params=[
                Param(key="name", required=True),
                Param(key="description"),
            ],
        )
        op = action_to_operation(svc, act)

        body = op["requestBody"]
        assert body["required"] is True
        schema = body["content"]["application/x-www-form-urlencoded"]["schema"]
        assert "name" in schema["properties"]
        assert "description" in schema["properties"]
        assert schema["required"] == ["name"]

    def test_post_no_required_params(self):
        svc = _make_service()
        act = _make_action(
            key="do_something",
            post=True,
            params=[Param(key="optional_field")],
        )
        op = action_to_operation(svc, act)

        body = op["requestBody"]
        assert body["required"] is False
        schema = body["content"]["application/x-www-form-urlencoded"]["schema"]
        assert "required" not in schema

    def test_no_params(self):
        svc = _make_service()
        act = _make_action()
        op = action_to_operation(svc, act)

        assert "parameters" not in op
        assert "requestBody" not in op


# -- webservices_to_openapi --


class TestWebservicesToOpenapi:
    def _make_services(self) -> list[WebService]:
        return [
            WebService(
                path="api/issues",
                description="Issues",
                actions=[
                    Action(key="search", description="Search issues"),
                    Action(key="create", post=True, description="Create issue"),
                    Action(key="internal_action", internal=True),
                ],
            ),
            WebService(
                path="api/rules",
                description="Rules",
                actions=[
                    Action(key="list", description="List rules"),
                ],
            ),
        ]

    def test_basic_conversion(self):
        services = self._make_services()
        spec = webservices_to_openapi(services, base_url="https://sonar.example.com")

        assert spec["openapi"] == "3.0.3"
        assert spec["servers"] == [{"url": "https://sonar.example.com"}]
        assert "bearerAuth" in spec["components"]["securitySchemes"]

        paths = spec["paths"]
        assert "/api/issues/search" in paths
        assert "/api/issues/create" in paths
        assert "/api/rules/list" in paths
        # Internal actions should be filtered out
        assert "/api/issues/internal_action" not in paths

    def test_read_only_excludes_post(self):
        services = self._make_services()
        spec = webservices_to_openapi(
            services, base_url="https://sonar.example.com", read_only=True
        )
        paths = spec["paths"]

        assert "/api/issues/search" in paths
        assert "/api/issues/create" not in paths

    def test_toolset_filter(self):
        services = self._make_services()
        spec = webservices_to_openapi(
            services, base_url="https://sonar.example.com", toolsets=["issues"]
        )
        paths = spec["paths"]

        assert "/api/issues/search" in paths
        assert "/api/rules/list" not in paths

    def test_empty_services(self):
        spec = webservices_to_openapi([], base_url="https://sonar.example.com")
        assert spec["paths"] == {}

    def test_methods_correct(self):
        services = self._make_services()
        spec = webservices_to_openapi(services, base_url="https://sonar.example.com")

        assert "get" in spec["paths"]["/api/issues/search"]
        assert "post" in spec["paths"]["/api/issues/create"]


# -- fetch_webservices --


class TestFetchWebservices:
    @pytest.mark.asyncio
    async def test_fetch_parses_response(self, respx_mock):
        mock_response = {
            "webServices": [
                {
                    "path": "api/issues",
                    "description": "Issues",
                    "actions": [
                        {"key": "search", "description": "Search"},
                    ],
                },
            ]
        }

        respx_mock.get(
            "https://sonar.test/api/webservices/list",
            params={"include_internals": "false"},
        ).mock(return_value=httpx.Response(200, json=mock_response))

        services = await fetch_webservices("https://sonar.test", "test-token")

        assert len(services) == 1
        assert services[0].path == "api/issues"
        assert services[0].actions[0].key == "search"

    @pytest.mark.asyncio
    async def test_fetch_empty_response(self, respx_mock):
        respx_mock.get(
            "https://sonar.test/api/webservices/list",
            params={"include_internals": "false"},
        ).mock(return_value=httpx.Response(200, json={"webServices": []}))

        services = await fetch_webservices("https://sonar.test", "test-token")
        assert services == []

    @pytest.mark.asyncio
    async def test_fetch_raises_on_error(self, respx_mock):
        respx_mock.get(
            "https://sonar.test/api/webservices/list",
            params={"include_internals": "false"},
        ).mock(return_value=httpx.Response(401))

        with pytest.raises(httpx.HTTPStatusError):
            await fetch_webservices("https://sonar.test", "bad-token")
