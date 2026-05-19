#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DeepSeek MCP Server
通过MCP协议连接DeepSeek官方API，用于代码审查和质量检查
"""

import json
import os
import sys
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

DEEPSEEK_BASE = "https://api.deepseek.com"
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")

_raw_key = os.environ.get("DEEPSEEK_API_KEY", "")
try:
    _raw_key.encode("latin-1")
except UnicodeEncodeError:
    sys.stderr.write(
        "ERROR: DEEPSEEK_API_KEY contains non-ASCII characters.\n"
        "Please check your Trae MCP config JSON and ensure the key value is ASCII-only.\n"
        "Common causes: smart quotes, zero-width characters, or encoding issues during copy-paste.\n"
    )
    sys.stderr.flush()
    _raw_key = _raw_key.encode("ascii", errors="ignore").decode("ascii")
DEEPSEEK_API_KEY = _raw_key.strip()


def deepseek_chat_completion(
    messages: List[Dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 8192,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """调用DeepSeek Chat Completion API"""
    if not DEEPSEEK_API_KEY:
        return {"error": "DEEPSEEK_API_KEY 未设置或已被过滤为无效值，请检查 key 是否含非 ASCII 字符"}

    url = f"{DEEPSEEK_BASE}/chat/completions"
    payload = {
        "model": model or DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            body = json.loads(response.read().decode("utf-8"))
            choice = body.get("choices", [{}])[0]
            message = choice.get("message", {})
            content = message.get("content", "")
            return {"content": content, "finish_reason": choice.get("finish_reason", "stop")}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return {"error": f"HTTP {e.code}: {err_body}"}
    except urllib.error.URLError as e:
        return {"error": str(e)}


def build_system_prompt(focus_areas: Optional[List[str]] = None) -> str:
    """构建系统提示词"""
    base = """你是一位资深代码审查专家，负责对代码进行全面质量检查。你的审查应涵盖以下方面：

1. **逻辑正确性**：代码逻辑是否准确，是否存在边界条件处理不当
2. **潜在Bug**：是否有可能导致运行时错误的隐患
3. **安全性**：是否存在注入、越权、敏感信息泄露等安全风险
4. **性能**：是否存在不必要的计算、内存浪费、I/O阻塞
5. **可维护性**：命名是否清晰、结构是否合理、是否有冗余代码
6. **最佳实践**：是否遵循语言/框架的惯用写法

审查结果请用中文输出，格式如下：
- 先给出总体评价（一句话概括）
- 然后按严重程度（🔴严重 → 🟡警告 → 🔵建议）逐条列出发现的问题
- 每条问题包含：位置说明 + 问题描述 + 修复建议
- 最后给出改进后的代码示例（如适用）

请保持专业、客观，不要过度吹毛求疵，也不要遗漏关键问题。"""

    if focus_areas:
        area_text = "、".join(focus_areas)
        base += f"\n\n本次审查请特别关注以下方面：{area_text}"

    return base


def handle_initialize(params: Dict, protocol_version: str = "2025-11-25") -> Dict[str, Any]:
    """处理initialize请求"""
    return {
        "protocolVersion": protocol_version,
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "deepseek-mcp",
            "version": "1.0.0"
        }
    }


def handle_list_tools(params: Dict) -> Dict[str, Any]:
    """处理tools/list请求"""
    return {
        "tools": [
            {
                "name": "code_review",
                "description": "对代码进行全面质量审查，包括逻辑正确性、潜在Bug、安全性、性能、可维护性和最佳实践",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "待审查的源代码"
                        },
                        "language": {
                            "type": "string",
                            "description": "编程语言，如 python, javascript, java, go 等"
                        },
                        "focus_areas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "需要特别关注的审查方面，如 ['安全性', '性能', '最佳实践']"
                        },
                        "context": {
                            "type": "string",
                            "description": "补充上下文信息，如代码用途、所属模块等"
                        }
                    },
                    "required": ["code"]
                }
            },
            {
                "name": "design_solution",
                "description": "针对需求做技术方案设计，给出至少3种方案并从性能稳定性、建设成本、远期迭代三个维度对比分析",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "requirement": {
                            "type": "string",
                            "description": "需求描述，越详细越好"
                        },
                        "tech_stack": {
                            "type": "string",
                            "description": "当前使用的技术栈，如 Go+Gin+MySQL+Redis"
                        },
                        "constraints": {
                            "type": "string",
                            "description": "约束条件，如性能要求、工期限制、兼容性要求等"
                        },
                        "existing_context": {
                            "type": "string",
                            "description": "现有系统上下文，如相关模块/接口/数据表信息"
                        }
                    },
                    "required": ["requirement"]
                }
            },
            {
                "name": "analyze_bugs",
                "description": "专门针对潜在的Bug、边界条件和异常处理进行深入分析",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "待分析的源代码"
                        },
                        "language": {
                            "type": "string",
                            "description": "编程语言"
                        },
                        "error_scenarios": {
                            "type": "string",
                            "description": "用户担心的具体错误场景，如 '并发访问'、'空指针' 等"
                        }
                    },
                    "required": ["code"]
                }
            }
        ]
    }


def handle_call_tool(name: str, arguments: Dict) -> Dict[str, Any]:
    """处理tools/call请求"""
    try:
        if name == "code_review":
            code = arguments.get("code", "")
            language = arguments.get("language", "")
            focus_areas = arguments.get("focus_areas")
            context = arguments.get("context", "")

            if not code.strip():
                return {"content": [{"type": "text", "text": "错误：代码内容不能为空"}]}

            user_prompt = f"请审查以下代码"
            if language:
                user_prompt += f"（语言：{language}）"
            if context:
                user_prompt += f"\n上下文：{context}"
            user_prompt += f"\n\n```\n{code}\n```"

            system_prompt = build_system_prompt(focus_areas)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            result = deepseek_chat_completion(messages, temperature=0.3, max_tokens=4096)
            if "error" in result:
                return {"content": [{"type": "text", "text": f"API错误: {result['error']}"}]}

            return {"content": [{"type": "text", "text": result["content"]}]}

        elif name == "analyze_bugs":
            code = arguments.get("code", "")
            language = arguments.get("language", "")
            error_scenarios = arguments.get("error_scenarios", "")

            if not code.strip():
                return {"content": [{"type": "text", "text": "错误：代码内容不能为空"}]}

            system_prompt = """你是一位高级Bug分析专家，专长于发现代码中的隐藏缺陷。请对代码进行深度分析，重点关注：

1. 边界条件处理（空值、零值、极限值、越界访问）
2. 异常处理完整性（是否吞掉了关键异常、异常类型是否匹配）
3. 并发/竞态条件（如适用）
4. 资源泄漏（文件句柄、连接、内存）
5. 类型安全（类型转换、隐式强制转换）
6. 输入验证（用户输入、外部数据）

用中文输出，按严重性排序，每条问题给出：
- 触发条件
- 实际影响
- 修复方案"""

            if error_scenarios:
                system_prompt += f"\n\n用户特别关注以下场景：{error_scenarios}"

            user_prompt = f"请深入分析以下代码的潜在Bug"
            if language:
                user_prompt += f"（语言：{language}）"
            user_prompt += f"\n\n```\n{code}\n```"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            result = deepseek_chat_completion(messages, temperature=0.3, max_tokens=4096)
            if "error" in result:
                return {"content": [{"type": "text", "text": f"API错误: {result['error']}"}]}

            return {"content": [{"type": "text", "text": result["content"]}]}

        elif name == "design_solution":
            requirement = arguments.get("requirement", "")
            tech_stack = arguments.get("tech_stack", "")
            constraints = arguments.get("constraints", "")
            existing_context = arguments.get("existing_context", "")

            if not requirement.strip():
                return {"content": [{"type": "text", "text": "错误：需求描述不能为空"}]}

            system_prompt = """你是一位资深技术架构师，专长于技术方案设计。请针对需求给出详细的技术方案。

要求：
1. 给出至少 3 种实现方案，每种方案包含核心思路和关键代码示例
2. 从以下三个维度对比分析每种方案：
   - 性能与稳定性
   - 建设成本（开发量、复杂度）
   - 远期迭代（可扩展性、可维护性）
3. 最后给出推荐方案及理由
4. 方案中涉及的模块/接口需明确调用关系和职责边界

输出格式：
- 先概述需求理解（一句）
- 然后逐方案展开，每方案含：思路 + 关键代码示例 + 三维度分析
- 最后是推荐结论"""

            user_prompt = f"需求：{requirement}"
            if tech_stack:
                user_prompt += f"\n当前技术栈：{tech_stack}"
            if constraints:
                user_prompt += f"\n约束条件：{constraints}"
            if existing_context:
                user_prompt += f"\n现有系统上下文：{existing_context}"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            result = deepseek_chat_completion(messages, temperature=0.5, max_tokens=8192)
            if "error" in result:
                return {"content": [{"type": "text", "text": f"API错误: {result['error']}"}]}

            return {"content": [{"type": "text", "text": result["content"]}]}

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
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.stderr.write("DeepSeek MCP Server starting...\n")
    sys.stderr.write(f"Model: {DEEPSEEK_MODEL}\n")

    if not DEEPSEEK_API_KEY:
        sys.stderr.write("WARNING: DEEPSEEK_API_KEY not set, API calls will fail\n")

    sys.stderr.write("Checking API connectivity...\n")
    test_result = deepseek_chat_completion(
        [{"role": "user", "content": "ping"}],
        temperature=0.0,
        max_tokens=4,
    )
    if "error" in test_result:
        sys.stderr.write(f"API connection test failed: {test_result['error']}\n")
    else:
        sys.stderr.write("DeepSeek API connection OK\n")

    sys.stderr.flush()

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            request = json.loads(line.strip())
            response = handle_request(request)
            if response:
                print(json.dumps(response, ensure_ascii=False), flush=True)
        except json.JSONDecodeError:
            continue
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"内部错误: {str(e)}"}
            }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
