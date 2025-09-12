from typing import List, Dict

from ultrarag.server import UltraRAG_MCP_Server

# Initialize server with authentication enabled
enable_auth = os.environ.get('ENABLE_AUTH', 'false').lower() == 'true'
auth_config = {
    'database_url': os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost:5432/strapi'),
    'jwt_secret': os.environ.get('JWT_SECRET', 'your-secret-key'),
    'api_key_header': 'X-API-Key'
}

app = UltraRAG_MCP_Server(
    "router",
    enable_auth=enable_auth,
    auth_config=auth_config
)


@app.tool(output="query_list")
def route1(query_list: List[str]) -> Dict[str, List[Dict[str, str]]]:
    query = [
        {"data": query, "state": "state1" if int(query) == 1 else "state2"}
        for query in query_list
    ]
    return {"query_list": query}


@app.tool(output="query_list")
def route2(query_list: List[str]) -> Dict[str, List[Dict[str, str]]]:
    query = [{"data": query, "state": "state2"} for query in query_list]
    return {"query_list": query}


@app.tool(output="ans_ls->ans_ls")
def ircot_check_end(ans_ls: List[str]) -> Dict[str, List[Dict[str, str]]]:
    ans_ls = [
        {
            "data": ans,
            "state": "complete" if "so the answer is" in ans.lower() else "incomplete",
        }
        for ans in ans_ls
    ]
    return {"ans_ls": ans_ls}


@app.tool(output="ans_ls->ans_ls")
def search_r1_check(ans_ls: List[str]) -> Dict[str, List[Dict[str, str]]]:
    """Check if the answer is complete or incomplete.
    Args:
        ans_ls (list): List of answers to check.
    Returns:
        dict: Dictionary containing the list of answers with their states.
    """

    def get_eos(text):
        import re

        if "<|endoftext|>" in text or "<|im_end|>" in text:
            return True
        else:
            return False

    ans_ls = [
        {
            "data": answer,
            "state": "complete" if get_eos(answer) else "incomplete",
        }
        for answer in ans_ls
    ]
    return {"ans_ls": ans_ls}


@app.tool(output="page_ls->page_ls")
def webnote_check_page(page_ls: List[str]) -> Dict[str, List[Dict[str, str]]]:
    """Check if the page is complete or incomplete.
    Args:
        page_ls (list): List of pages to check.
    Returns:
        dict: Dictionary containing the list of pages with their states.
    """
    page_ls = [
        {
            "data": page,
            "state": "incomplete" if "to be filled" in page.lower() else "complete",
        }
        for page in page_ls
    ]
    return {"page_ls": page_ls}


@app.tool(output="ans_ls->ans_ls")
def r1_searcher_check(ans_ls: List[str]) -> Dict[str, List[Dict[str, str]]]:
    """Check if the answer is complete or incomplete.
    Args:
        ans_ls (list): List of answers to check.
    Returns:
        dict: Dictionary containing the list of answers with their states.
    """

    def get_eos(text):
        import re

        if "<|endoftext|>" in text or "<|im_end|>" in text or "</answer>" in text:
            return True
        else:
            return False

    ans_ls = [
        {
            "data": answer,
            "state": "complete" if get_eos(answer) else "incomplete",
        }
        for answer in ans_ls
    ]
    return {"ans_ls": ans_ls}


@app.tool(output="ans_ls->ans_ls")
def search_o1_check(ans_ls: List[str]) -> Dict[str, List[Dict[str, str]]]:
    def get_eos(text):

        if "<|im_end|>" in text:
            return True
        elif "<|end_search_query|>" in text:
            return False

    ans_ls = [
        {
            "data": answer,
            "state": "stop" if get_eos(answer) else "retrieve",
        }
        for answer in ans_ls
    ]
    return {"ans_ls": ans_ls}


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='UltraRAG MCP Server - Router')
    parser.add_argument('--transport', default='stdio', choices=['stdio', 'http'], help='Transport type')
    parser.add_argument('--port', type=int, default=8009, help='Port for HTTP transport')
    parser.add_argument('--host', default='0.0.0.0', help='Host for HTTP transport')
    
    args = parser.parse_args()
    
    if args.transport == 'http':
        app.run(transport="http", host=args.host, port=args.port)
    else:
        app.run(transport="stdio")
