"""Configuration management for Grafana Publisher."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv


class GrafanaSource(BaseModel):
    """Grafana alert source configuration."""
    name: str
    folder_id: str
    rules_group: str
    labels_filter: Dict[str, str] = Field(default_factory=dict)


class GrafanaConfig(BaseModel):
    """Grafana configuration."""
    url: str
    token: str
    verify_ssl: bool = True
    timeout: int = 30
    sources: List[GrafanaSource]
    
    @field_validator("token")
    @classmethod
    def expand_env_var(cls, v: str) -> str:
        """Expand environment variables in token."""
        if v.startswith("${") and v.endswith("}"):
            var_name = v[2:-1]
            return os.getenv(var_name, v)
        return v


class FieldMapping(BaseModel):
    """Field mapping configuration."""
    type: str
    field_name: str
    default: Optional[str] = None


class CacheConfig(BaseModel):
    """Cache configuration."""
    enabled: bool = True
    ttl: int = 86400
    path: str = "~/.grafana_publisher_cache.json"
    
    @field_validator("path")
    @classmethod
    def expand_path(cls, v: str) -> str:
        """Expand user home directory in path."""
        return str(Path(v).expanduser())


class ClickUpConfig(BaseModel):
    """ClickUp publisher configuration."""
    enabled: bool = True
    api_url: str
    token: str
    list_id: str
    field_mappings: Dict[str, FieldMapping]
    cache: CacheConfig
    
    @field_validator("token")
    @classmethod
    def expand_env_var(cls, v: str) -> str:
        """Expand environment variables in token."""
        if v.startswith("${") and v.endswith("}"):
            var_name = v[2:-1]
            return os.getenv(var_name, v)
        return v


class JiraConfig(BaseModel):
    """Jira publisher configuration."""
    enabled: bool = False
    url: str
    token: str
    project_key: str
    issue_type: str = "Incident"
    
    @field_validator("token")
    @classmethod
    def expand_env_var(cls, v: str) -> str:
        """Expand environment variables in token."""
        if v.startswith("${") and v.endswith("}"):
            var_name = v[2:-1]
            return os.getenv(var_name, v)
        return v


class AlertRule(BaseModel):
    """Alert processing rule."""
    name: str
    patterns: List[str]
    priority: str = "medium"
    template: str
    fields: Dict[str, Any] = Field(default_factory=dict)


class Template(BaseModel):
    """Ticket template."""
    title: str
    description: str


class DeduplicationConfig(BaseModel):
    """Deduplication configuration."""
    enabled: bool = True
    strategy: str = "task_name"
    check_existing: bool = True


class ModesConfig(BaseModel):
    """Operating modes configuration."""
    dry_run: bool = False
    interactive: bool = False
    verbose: bool = False


class OutputConfig(BaseModel):
    """Output configuration."""
    format: str = "rich"
    file: Optional[str] = None


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    file: str = "grafana_publisher.log"
    format: str = "json"


class SettingsConfig(BaseModel):
    """General settings."""
    deduplication: DeduplicationConfig
    modes: ModesConfig
    output: OutputConfig
    logging: LoggingConfig


class Config(BaseModel):
    """Main configuration model."""
    grafana: GrafanaConfig
    publishers: Dict[str, Any]
    alert_rules: List[AlertRule]
    templates: Dict[str, Template]
    settings: SettingsConfig
    
    @classmethod
    def from_file(cls, config_path: Path) -> "Config":
        """Load configuration from YAML file."""
        # Load environment variables
        load_dotenv()
        
        with open(config_path) as f:
            data = yaml.safe_load(f)
        
        # Parse publishers separately for flexibility
        publishers = {}
        if "publishers" in data:
            if "clickup" in data["publishers"]:
                publishers["clickup"] = ClickUpConfig(**data["publishers"]["clickup"])
            if "jira" in data["publishers"]:
                publishers["jira"] = JiraConfig(**data["publishers"]["jira"])
        
        # Parse templates
        templates = {}
        if "templates" in data:
            for name, template_data in data["templates"].items():
                templates[name] = Template(**template_data)
        
        return cls(
            grafana=GrafanaConfig(**data["grafana"]),
            publishers=publishers,
            alert_rules=[AlertRule(**rule) for rule in data.get("alert_rules", [])],
            templates=templates,
            settings=SettingsConfig(**data.get("settings", {}))
        )
    
    def get_publisher(self, name: str) -> Optional[Any]:
        """Get publisher configuration by name."""
        return self.publishers.get(name)