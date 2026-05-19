#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ollama MCP Server
通过MCP协议连接远程Ollama服务
"""

import json
import sys
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

OLLAMA_HOST = "http://192.168.0.64:11434"

session_history: Dict[str, List[Dict[str, str]]] = {}


def ollama_request(endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
    """向Ollama发送请求"""
    url = f"{OLLAMA_HOST}{endpoint}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8") if data else None,
        headers={"Content-Type": "application/json"},
        method="POST" if data else "GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return {"error": str(e)}


def handle_initialize(params: Dict, protocol_version: str = "2025-11-25") -> Dict[str, Any]:
    """处理initialize请求"""
    return {
        "protocolVersion": protocol_version,
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "ollama-mcp",
            "version": "1.0.0"
        }
    }


def handle_list_tools(params: Dict) -> Dict[str, Any]:
    """处理tools/list请求"""
    return {
        "tools": [
            {
                "name": "list_models",
                "description": "列出Ollama中所有已安装的模型",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "list_running_models",
                "description": "列出当前正在运行的模型",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "chat",
                "description": "使用指定模型进行对话，支持会话记忆",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "model": {
                            "type": "string",
                            "description": "模型名称，如 qwen3q6-v3:latest"
                        },
                        "session_id": {
                            "type": "string",
                            "description": "会话ID，用于保持对话上下文"
                        },
                        "messages": {
                            "type": "array",
                            "description": "消息列表，每条消息包含role和content"
                        },
                        "stream": {
                            "type": "boolean",
                            "description": "是否使用流式输出",
                            "default": False
                        }
                    },
                    "required": ["model", "messages"]
                }
            },
            {
                "name": "generate",
                "description": "使用指定模型生成文本",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "model": {
                            "type": "string",
                            "description": "模型名称"
                        },
                        "prompt": {
                            "type": "string",
                            "description": "输入提示"
                        },
                        "stream": {
                            "type": "boolean",
                            "description": "是否使用流式输出",
                            "default": False
                        }
                    },
                    "required": ["model", "prompt"]
                }
            },
            {
                "name": "clear_session",
                "description": "清除指定会话的历史记录",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "要清除的会话ID，不传则清除默认会话"
                        }
                    }
                }
            },
            {
                "name": "list_sessions",
                "description": "列出所有活跃的会话",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    }


def handle_call_tool(name: str, arguments: Dict) -> Dict[str, Any]:
    """处理tools/call请求"""
    try:
        if name == "list_models":
            result = ollama_request("/api/tags")
            if "error" in result:
                return {"content": [{"type": "text", "text": f"错误: {result['error']}"}]}
            models = result.get("models", [])
            if not models:
                return {"content": [{"type": "text", "text": "没有已安装的模型"}]}
            model_list = "\n".join([f"- {m['name']}" for m in models])
            return {"content": [{"type": "text", "text": f"已安装的模型:\n{model_list}"}]}

        elif name == "list_running_models":
            result = ollama_request("/api/ps")
            if "error" in result:
                return {"content": [{"type": "text", "text": f"错误: {result['error']}"}]}
            models = result.get("models", [])
            if not models:
                return {"content": [{"type": "text", "text": "没有正在运行的模型"}]}
            model_list = "\n".join([f"- {m['name']}" for m in models])
            return {"content": [{"type": "text", "text": f"正在运行的模型:\n{model_list}"}]}

        elif name == "chat":
            model = arguments.get("model")
            session_id = arguments.get("session_id", "default")
            messages = arguments.get("messages", [])
            
            history = session_history.get(session_id, [])
            all_messages = history + messages
            
            result = ollama_request("/api/chat", {
                "model": model,
                "messages": all_messages,
                "stream": False
            })
            
            if "error" in result:
                return {"content": [{"type": "text", "text": f"错误: {result['error']}"}]}
            
            response_message = result.get("message", {})
            content = response_message.get("content", "")
            
            if session_id != "default":
                for msg in messages:
                    if msg.get("role") == "user":
                        history.append(msg)
                history.append({"role": "assistant", "content": content})
                session_history[session_id] = history
            
            return {"content": [{"type": "text", "text": content}]}

        elif name == "generate":
            model = arguments.get("model")
            prompt = arguments.get("prompt")
            result = ollama_request("/api/generate", {
                "model": model,
                "prompt": prompt,
                "stream": False
            })
            if "error" in result:
                return {"content": [{"type": "text", "text": f"错误: {result['error']}"}]}
            content = result.get("response", "")
            return {"content": [{"type": "text", "text": content}]}

        elif name == "clear_session":
            session_id = arguments.get("session_id", "default")
            if session_id in session_history:
                del session_history[session_id]
                return {"content": [{"type": "text", "text": f"已清除会话 {session_id} 的历史记录"}]}
            return {"content": [{"type": "text", "text": f"会话 {session_id} 不存在或已经为空"}]}

        elif name == "list_sessions":
            if not session_history:
                return {"content": [{"type": "text", "text": "当前没有活跃的会话"}]}
            session_list = "\n".join([f"- {sid}: {len(msgs)} 条消息" for sid, msgs in session_history.items()])
            return {"content": [{"type": "text", "text": f"活跃会话:\n{session_list}"}]}

        else:
            return {"content": [{"type": "text", "text": f"未知工具: {name}"}]}

    except Exception as e:
        return {"content": [{"type": "text", "text": f"执行错误: {str(e)}"}]}


def handle_request(request: Dict) -> Optional[Dict]:
    """处理单个请求"""
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params", {})
    protocol_version = params.get("protocolVersion", "2025-11-25")

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": request_id, "result": handle_initialize(params, protocol_version)}
    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": handle_list_tools(params)}
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        return {"jsonrpc": "2.0", "id": request_id, "result": handle_call_tool(tool_name, arguments)}
    elif method == "notifications/initialized":
        return None
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"未知方法: {method}"}
        }


def main():
    """主循环"""
    import sys
    import socket
    sys.stderr.write("Ollama MCP Server starting...\n")
    sys.stderr.flush()
    
    host = "192.168.0.64"
    port = 11434
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            sys.stderr.write(f"Connected to Ollama at {host}:{port}\n")
        else:
            sys.stderr.write(f"Cannot connect to Ollama at {host}:{port}\n")
    except Exception as e:
        sys.stderr.write(f"Connection test error: {e}\n")
    sys.stderr.flush()
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            request = json.loads(line.strip())
            response = handle_request(request)
            if response:
                print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            continue
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(json.dumps({
                "error": {"code": -32603, "message": f"内部错误: {str(e)}"}
            }), flush=True)


if __name__ == "__main__":
    main()
