import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from fastmcp.exceptions import NotFoundError, ToolError
from ultrarag.server import UltraRAG_MCP_Server

# Initialize server with authentication enabled
enable_auth = os.environ.get('ENABLE_AUTH', 'false').lower() == 'true'
auth_config = {
    'database_url': os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost:5432/strapi'),
    'jwt_secret': os.environ.get('JWT_SECRET', 'your-secret-key'),
    'api_key_header': 'X-API-Key'
}

app = UltraRAG_MCP_Server(
    "benchmark",
    enable_auth=enable_auth,
    auth_config=auth_config
)


@staticmethod
def _load_data_from_file(
    path: str | Path,
    limit: int,
) -> List[Dict[str, Any]]:
    data = []
    if path.endswith(".jsonl"):
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= limit and limit > 0:
                    break
                data.append(json.loads(line))
    elif path.endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if limit > 0:
                data = data[:limit]
    elif path.endswith(".parquet"):
        df = pd.read_parquet(path)
        data = df.to_dict(orient="records")
        if limit > 0:
            data = data[:limit]
    else:
        app.logger.error(
            f"Unsupported file format: ({path}). Supported: .jsonl, .json, .parquet"
        )
        raise ToolError(
            f"Unsupported file format: ({path}). Supported: .jsonl, .json, .parquet"
        )

    app.logger.info(f"Loaded from {path}")
    app.logger.debug(f"_load_data_from_file data: {data}")
    return data


def _load_from_local(
    path: str,
    key_map: Dict[str, str],
    limit: int,
    is_shuffle: bool = False,
    seed: int = 42,
) -> Dict[str, List[Any]]:

    data = _load_data_from_file(path, -1 if is_shuffle else limit)
    ret: Dict[str, List[Any]] = {}
    for alias, original_key in key_map.items():
        ret[alias] = [item[original_key] for item in data if original_key in item]

    if is_shuffle:
        length = len(next(iter(ret.values())))
        idx = list(range(length))
        import random

        random.seed(seed)
        random.shuffle(idx)
        idx = idx if limit == -1 else idx[:limit]
        for k in ret:
            ret[k] = [ret[k][i] for i in idx]
    else:
        if limit != -1:
            for k in ret:
                ret[k] = ret[k][:limit]

    app.logger.debug(ret)
    return ret


@app.tool(output="benchmark->q_ls,gt_ls")
def get_data(
    benchmark: Dict[str, Any],
) -> Dict[str, List[Any]]:
    app.logger.info(f"Loading data: {benchmark.get('path')}")

    path = benchmark.get("path")
    key_map = benchmark.get("key_map", {})
    is_shuffle = benchmark.get("shuffle", False)
    seed = benchmark.get("seed", 42)
    limit = benchmark.get("limit", -1)

    if not path:
        err_msg = f"Benchmark path: {path} is required"
        app.logger.error(err_msg)
        raise NotFoundError(err_msg)

    if not key_map:
        err_msg = f"Benchmark parameter key_map: {key_map} is required"
        app.logger.error(err_msg)
        raise ToolError(err_msg)

    elif not isinstance(key_map, dict):
        err_msg = f"Benchmark parameter key_map: {key_map} must be a dictionary"
        app.logger.error(err_msg)
        raise ToolError(err_msg)

    elif len(key_map.keys()) == 0:
        err_msg = (
            f"Benchmark parameter key_map: {key_map} must contain at least one key"
        )
        app.logger.error(err_msg)
        raise ToolError(err_msg)

    if not isinstance(limit, int) or limit < -1:
        err_msg = (
            f"Benchmark parameter limit: {limit} must be a non-negative integer or -1"
        )
        app.logger.error(err_msg)
        raise ToolError(err_msg)

    if limit == 0:
        err_msg = f"Benchmark parameter limit: {limit} cannot be 0"
        app.logger.error(err_msg)
        raise ToolError(err_msg)

    data = _load_from_local(path, key_map, limit, is_shuffle, seed)

    app.logger.info(f"Loaded benchmark: {benchmark.get('name'),benchmark.get('path')}")
    app.logger.debug(f"Benchmark: {data}")
    return data


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='UltraRAG MCP Server - Benchmark')
    parser.add_argument('--transport', default='stdio', choices=['stdio', 'http'], help='Transport type')
    parser.add_argument('--port', type=int, default=8006, help='Port for HTTP transport')
    parser.add_argument('--host', default='0.0.0.0', help='Host for HTTP transport')
    
    args = parser.parse_args()
    
    if args.transport == 'http':
        app.run(transport="http", host=args.host, port=args.port)
    else:
        app.run(transport="stdio")
