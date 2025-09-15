from __future__ import annotations
import yaml
import os
from pathlib import Path
import inspect
from functools import partial
from contextlib import AbstractAsyncContextManager
from types import SimpleNamespace, EllipsisType
from typing import Any, Literal, Callable, List

from mcp.types import AnyFunction, ToolAnnotations, TypeAlias
from mcp.server.lowlevel.server import LifespanResultT
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.tools.tool_transform import ToolTransformConfig
from fastmcp import FastMCP
from fastmcp.prompts import Prompt
from fastmcp.server.auth.auth import OAuthProvider
from fastmcp.client import Client
from fastmcp.tools.tool import Tool
import logging

# Import authentication modules
try:
    from auth.auth_manager import AuthManager
    from auth.api_key_validator import APIKeyValidator
    from auth.database_client import DatabaseClient
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False

NotSet = ...
NotSetT: TypeAlias = EllipsisType

DuplicateBehavior = Literal["warn", "error", "replace", "ignore"]
Transport = Literal["stdio", "http", "sse", "streamable-http"]
import atexit, asyncio

from ultrarag.mcp_logging import get_logger


class UltraRAG_MCP_Server(FastMCP):
    def __init__(
        self,
        name: str | None = None,
        instructions: str | None = None,
        *,
        version: str | None = None,
        auth: OAuthProvider | None = None,
        middleware: list[Middleware] | None = None,
        lifespan: (
            Callable[
                [FastMCP[LifespanResultT]],
                AbstractAsyncContextManager[LifespanResultT],
            ]
            | None
        ) = None,
        tool_serializer: Callable[[Any], str] | None = None,
        on_duplicate_tools: DuplicateBehavior | None = None,
        on_duplicate_resources: DuplicateBehavior | None = None,
        on_duplicate_prompts: DuplicateBehavior | None = None,
        resource_prefix_format: Literal["protocol", "path"] | None = None,
        tool_transformations: dict[str, ToolTransformConfig] | None = None,
        mask_error_details: bool | None = None,
        tools: list[Tool | Callable[..., Any]] | None = None,
        dependencies: list[str] | None = None,
        include_tags: set[str] | None = None,
        exclude_tags: set[str] | None = None,
        include_fastmcp_meta: bool | None = None,
        log_level: str | None = None,
        debug: bool | None = None,
        host: str | None = None,
        port: int | None = None,
        sse_path: str | None = None,
        message_path: str | None = None,
        streamable_http_path: str | None = None,
        json_response: bool | None = None,
        stateless_http: bool | None = None,
        # Authentication parameters
        enable_auth: bool = False,
        auth_config: dict | None = None,
    ):
        name = name or "UltraRAG"
        level = os.environ.get("log_level", "warn")
        self.logger = get_logger(name, level)

        # Initialize authentication
        self.enable_auth = enable_auth
        self.auth_manager = None
        self.api_key_validator = None
        
        if enable_auth and AUTH_AVAILABLE:
            try:
                # Initialize authentication components
                self.auth_manager = AuthManager()
                self.api_key_validator = APIKeyValidator()
                    
                self.logger.info(f"Authentication enabled for {name}")
            except Exception as e:
                self.logger.error(f"Failed to initialize authentication: {e}")
                self.enable_auth = False
        elif enable_auth and not AUTH_AVAILABLE:
            self.logger.warning("Authentication requested but auth modules not available")
            self.enable_auth = False

        # Prepare middleware: attach auth middleware when enabled
        combined_middleware = middleware[:] if middleware else []
        self.logger.info(f"Auth status - enable_auth: {self.enable_auth}, AUTH_AVAILABLE: {AUTH_AVAILABLE}")
        if self.enable_auth and AUTH_AVAILABLE:
            try:
                auth_middleware = self._create_auth_middleware()
                combined_middleware.append(auth_middleware)
                self.logger.info(f"Authentication middleware added successfully. Total middleware count: {len(combined_middleware)}")
            except Exception as e:
                self.logger.error(f"Failed to attach auth middleware: {e}")

        super().__init__(
            name,
            instructions,
            version=version,
            auth=auth,
            middleware=combined_middleware,
            lifespan=lifespan,
            tool_serializer=tool_serializer,
            on_duplicate_tools=on_duplicate_tools,
            on_duplicate_resources=on_duplicate_resources,
            on_duplicate_prompts=on_duplicate_prompts,
            resource_prefix_format=resource_prefix_format,
            mask_error_details=mask_error_details,
            tools=tools,
            tool_transformations=tool_transformations,
            include_fastmcp_meta=include_fastmcp_meta,
            dependencies=dependencies,
            include_tags=include_tags,
            exclude_tags=exclude_tags,
            log_level=log_level,
            debug=debug,
            host=host,
            port=port,
            sse_path=sse_path,
            message_path=message_path,
            streamable_http_path=streamable_http_path,
            json_response=json_response,
            stateless_http=stateless_http,
        )
        self.output = {}
        self.fn_meta: dict[str, dict[str, Any]] = {}
        self.prompt_meta: dict[str, dict[str, Any]] = {}
        self.tool(self.build, name="build")

    def load_config(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def authenticate_request(self, request_headers: dict) -> bool:
        """
        Authenticate a request using API key or JWT token
        Returns True if authentication is successful, False otherwise
        """
        if not self.enable_auth or not self.auth_manager:
            return True  # No authentication required
        
        try:
            # Check for API key in headers
            api_key = request_headers.get('X-API-Key') or request_headers.get('Authorization')
            
            if api_key:
                # Remove 'Bearer ' prefix if present
                if api_key.startswith('Bearer '):
                    api_key = api_key[7:]
                
                # Validate API key
                if self.api_key_validator and self.api_key_validator.validate_api_key(api_key):
                    self.logger.debug("API key authentication successful")
                    return True
            
            # Check for JWT token
            jwt_token = request_headers.get('Authorization')
            if jwt_token and jwt_token.startswith('Bearer '):
                jwt_token = jwt_token[7:]
                if self.auth_manager.validate_jwt_token(jwt_token):
                    self.logger.debug("JWT token authentication successful")
                    return True
            
            self.logger.warning("Authentication failed: No valid credentials provided")
            return False
            
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False

    def tool(
        self,
        name_or_fn: str | AnyFunction | None = None,
        *,
        output: str | None = None,
        name: str | None = None,
        title: str | None = None,
        description: str | None = None,
        tags: set[str] | None = None,
        output_schema: dict[str, Any] | None | NotSetT = NotSet,
        annotations: ToolAnnotations | dict[str, Any] | None = None,
        exclude_args: list[str] | None = None,
        meta: dict[str, Any] | None = None,
        enabled: bool | None = None,
    ):
        if output is not None:
            if annotations is None:
                annotations = {"output": output}
            elif isinstance(annotations, dict):
                annotations = annotations | {"output": output}
            else:
                annotations.output = output

        return super().tool(
            name_or_fn,
            name=name,
            title=title,
            output_schema=output_schema,
            description=description,
            tags=tags,
            annotations=annotations,
            exclude_args=exclude_args,
            meta=meta,
            enabled=enabled,
        )

    def prompt(
        self,
        name_or_fn: str | AnyFunction | None = None,
        *,
        output: str | None = None,
        name: str | None = None,
        description: str | None = None,
        tags: set[str] | None = None,
        enabled: bool | None = None,
    ):

        # if output is not None:
        if isinstance(name_or_fn, classmethod):
            raise ValueError(
                inspect.cleandoc(
                    """
                    To decorate a classmethod, first define the method and then call
                    prompt() directly on the method instead of using it as a
                    decorator. See https://gofastmcp.com/patterns/decorating-methods
                    for examples and more information.
                    """
                )
            )

        # Determine the actual name and function based on the calling pattern
        if inspect.isroutine(name_or_fn):
            # Case 1: @prompt (without parens) - function passed directly as decorator
            # Case 2: direct call like prompt(fn, name="something")
            fn = name_or_fn
            prompt_name = name  # Use keyword name if provided, otherwise None

            if not hasattr(self, "_pending_output"):
                self._pending_output: dict[int, str] = {}
            self._pending_output[name or fn.__name__] = output

            # Register the prompt immediately
            prompt = Prompt.from_function(
                fn=fn,
                name=prompt_name,
                description=description,
                tags=tags,
                enabled=enabled,
            )
            self.add_prompt(prompt)

            return prompt

        elif isinstance(name_or_fn, str):
            # Case 3: @prompt("custom_name") - name passed as first argument
            if name is not None:
                raise TypeError(
                    "Cannot specify both a name as first argument and as keyword argument. "
                    f"Use either @prompt('{name_or_fn}') or @prompt(name='{name}'), not both."
                )
            prompt_name = name_or_fn
        elif name_or_fn is None:
            # Case 4: @prompt() or @prompt(name="something") - use keyword name
            prompt_name = name
        else:
            raise TypeError(
                f"First argument to @prompt must be a function, string, or None, got {type(name_or_fn)}"
            )

        # Return partial for cases where we need to wait for the function
        return partial(
            self.prompt,
            name=prompt_name,
            description=description,
            tags=tags,
            enabled=enabled,
            output=output,
        )

    def add_prompt(self, prompt: Prompt) -> None:
        fn = prompt.fn
        fn_name = fn.__name__

        sig = inspect.signature(fn)
        param_names = [
            p.name
            for p in sig.parameters.values()
            if p.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            )
        ]
        output_val = self._pending_output.pop(fn_name, None)
        self.prompt_meta[prompt.name or fn_name] = {
            "fn_name": fn_name,
            "params": param_names,
            "output": output_val,
        }

        super().add_prompt(prompt)

    def add_tool(self, tool: Tool) -> None:
        fn = tool.fn
        fn_name = fn.__name__
        if fn_name != "build":
            sig = inspect.signature(fn)
            param_names = [
                p.name
                for p in sig.parameters.values()
                if p.kind
                in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.KEYWORD_ONLY,
                )
            ]
            try:
                output = tool.annotations.output
            except:
                output = None
            self.fn_meta[tool.name or fn_name] = {
                "fn_name": fn_name,
                "params": param_names,
                "output": output,
            }

        super().add_tool(tool)

    def _make_io_mapping(
        self, params: list[str], io_spec: str | None, param_cfg: dict
    ) -> dict[str, str]:
        if io_spec:
            in_specs = [p.strip() for p in io_spec.split(",")]
        else:
            in_specs = params

        mapping = {}
        for key, spec in zip(params, in_specs):
            if spec in param_cfg and not spec.startswith("$"):
                spec = "$" + spec
            mapping[key] = spec
        return mapping

    def _build_entry(self, meta: dict, param_cfg: dict):
        entry: dict[str, Any] = {}
        print(meta["output"])
        if meta["output"]:
            parts = [span.strip() for span in meta["output"].split("->")]
            assert len(parts) <= 2, f"Output format error: {meta['output']}"
            entry["input"] = self._make_io_mapping(
                meta["params"], parts[0] if len(parts) == 2 else None, param_cfg
            )
            if parts[-1].strip() and not parts[-1].strip().lower() == "none":
                entry["output"] = [
                    (
                        "$" + p.strip()
                        if p.strip() in param_cfg and not p.strip().startswith("$")
                        else p.strip()
                    )
                    for p in parts[-1].split(",")
                ]
        else:
            entry["input"] = self._make_io_mapping(meta["params"], None, param_cfg)
        return entry

    def build(self, parameter_file: str):
        cfg_path = Path(parameter_file)
        base_dir = cfg_path.parent
        srv_name = base_dir.name
        self.param_cfg = self.load_config(str(cfg_path)) if cfg_path.exists() else {}
        out_path = base_dir / "server.yaml"
        build_yaml = {
            "path": self.param_cfg.get(
                "path", str(base_dir / "src" / f"{srv_name}.py")
            ),
            "parameter": parameter_file,
            "tools": {
                name: self._build_entry(self.fn_meta[name], self.param_cfg)
                for name in self.fn_meta
            },
            "prompts": {
                name: self._build_entry(self.prompt_meta[name], self.param_cfg)
                for name in self.prompt_meta
            },
        }

        if not Path(build_yaml["path"]).exists():
            raise FileNotFoundError(f"Server code not found: {build_yaml['path']}")

        yaml.safe_dump(
            build_yaml, out_path.open("w"), allow_unicode=True, sort_keys=False
        )

    def run(
        self,
        transport: Transport | None = None,
        show_banner: bool = False,
        **transport_kwargs: Any,
    ) -> None:
        # Add authentication middleware if enabled
        if self.enable_auth and transport == "http":
            # Create authentication middleware
            auth_middleware = self._create_auth_middleware()
            if auth_middleware:
                # Add to existing middleware list
                if self.middleware is None:
                    self.middleware = []
                self.middleware.append(auth_middleware)
        
        super().run(
            transport=transport,
            show_banner=show_banner,
            **transport_kwargs,
        )
    
    def _create_auth_middleware(self):
        """Create authentication middleware for HTTP requests (FastMCP)."""
        if not self.enable_auth or not AUTH_AVAILABLE:
            return None

        server_ref = self

        async def auth_middleware(context: MiddlewareContext, next_callable=None):
            server_ref.logger.info("Auth middleware called!")
            # Best-effort extraction of headers from context
            headers: dict[str, str] = {}
            try:
                req = getattr(context, "request", None)
                if req is not None and hasattr(req, "headers"):
                    headers = dict(req.headers)  # type: ignore[arg-type]
                elif hasattr(context, "headers"):
                    headers = dict(getattr(context, "headers"))  # type: ignore[arg-type]
                server_ref.logger.info(f"Extracted headers: {headers}")
            except Exception as e:
                server_ref.logger.error(f"Failed to extract headers: {e}")
                headers = {}

            # Authenticate
            if not server_ref.authenticate_request(headers):
                # Fallback 401 response; different FastMCP versions may have different APIs
                try:
                    from fastmcp.server.middleware import MiddlewareResponse  # type: ignore
                    return MiddlewareResponse(
                        status_code=401,
                        headers={"Content-Type": "application/json"},
                        body='{"error":"Unauthorized","message":"Authentication required. Provide valid API key or JWT."}'
                    )
                except Exception:
                    raise PermissionError("Unauthorized")

            # Continue the pipeline
            if next_callable is not None:
                return await next_callable()
            if hasattr(context, "next"):
                return await context.next()  # type: ignore[attr-defined]
            return None

        return auth_middleware


logging.getLogger("mcp").setLevel(logging.WARNING)
