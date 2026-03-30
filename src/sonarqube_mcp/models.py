from typing import Optional, List
from pydantic import BaseModel, Field


class Param(BaseModel):
    """Represents a parameter for a web service action."""
    key: str = Field(..., description="Parameter key")
    description: Optional[str] = Field(None, description="Parameter description")
    required: bool = Field(False, description="Whether the parameter is required")
    internal: bool = Field(False, description="Whether the parameter is internal")
    since: Optional[str] = Field(None, description="Since which version the parameter is available")
    maximumLength: Optional[int] = Field(None, description="Maximum length of the parameter")
    exampleValue: Optional[str] = Field(None, description="Example value for the parameter")


class ChangeLog(BaseModel):
    """Represents a changelog entry for an action."""
    description: str = Field(..., description="Description of the change")
    version: str = Field(..., description="Version when the change was introduced")


class Action(BaseModel):
    """Represents an action (endpoint) within a web service."""
    key: str = Field(..., description="Action key")
    description: Optional[str] = Field(None, description="Action description")
    since: Optional[str] = Field(None, description="Since which version the action is available")
    deprecatedSince: Optional[str] = Field(None, description="Version when the action was deprecated")
    internal: bool = Field(False, description="Whether the action is internal")
    post: bool = Field(False, description="Whether the action uses POST method")
    hasResponseExample: bool = Field(False, description="Whether a response example is available")
    changelog: List[ChangeLog] = Field(default_factory=list, description="List of changelog entries")
    params: List[Param] = Field(default_factory=list, description="List of parameters for this action")


class WebService(BaseModel):
    """Represents a SonarQube web service."""
    path: str = Field(..., description="Service path")
    since: Optional[str] = Field(None, description="Since which version the service is available")
    description: Optional[str] = Field(None, description="Service description")
    actions: List[Action] = Field(default_factory=list, description="List of actions in this service")
