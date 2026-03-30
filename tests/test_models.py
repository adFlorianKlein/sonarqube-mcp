import pytest
from pydantic import ValidationError

from models import Action, ChangeLog, Param, WebService


class TestParam:
    def test_minimal(self):
        p = Param(key="project")
        assert p.key == "project"
        assert p.required is False
        assert p.internal is False
        assert p.description is None
        assert p.maximumLength is None
        assert p.exampleValue is None

    def test_full(self):
        p = Param(
            key="project",
            description="Project key",
            required=True,
            internal=False,
            since="6.3",
            maximumLength=400,
            exampleValue="my_project",
        )
        assert p.key == "project"
        assert p.required is True
        assert p.maximumLength == 400
        assert p.exampleValue == "my_project"

    def test_missing_key_raises(self):
        with pytest.raises(ValidationError):
            Param()


class TestChangeLog:
    def test_valid(self):
        cl = ChangeLog(description="Added param X", version="9.1")
        assert cl.description == "Added param X"
        assert cl.version == "9.1"

    def test_missing_fields_raises(self):
        with pytest.raises(ValidationError):
            ChangeLog()


class TestAction:
    def test_minimal(self):
        a = Action(key="search")
        assert a.key == "search"
        assert a.post is False
        assert a.internal is False
        assert a.params == []
        assert a.changelog == []

    def test_with_params_and_changelog(self):
        a = Action(
            key="create",
            description="Create issue",
            post=True,
            params=[Param(key="name", required=True)],
            changelog=[ChangeLog(description="Initial", version="1.0")],
        )
        assert a.post is True
        assert len(a.params) == 1
        assert a.params[0].key == "name"
        assert len(a.changelog) == 1

    def test_deprecated(self):
        a = Action(key="old_search", deprecatedSince="8.0")
        assert a.deprecatedSince == "8.0"


class TestWebService:
    def test_minimal(self):
        ws = WebService(path="api/issues")
        assert ws.path == "api/issues"
        assert ws.actions == []
        assert ws.description is None

    def test_with_actions(self):
        ws = WebService(
            path="api/issues",
            description="Issues service",
            since="3.6",
            actions=[
                Action(key="search"),
                Action(key="create", post=True),
            ],
        )
        assert len(ws.actions) == 2
        assert ws.actions[1].post is True
