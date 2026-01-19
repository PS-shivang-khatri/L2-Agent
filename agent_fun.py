import asyncio, json, sys
from typing import Dict, Any, List
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from ollama import chat  # pip install ollama

SYSTEM = (
    "You are a helpful assistant. You have access to the following tools and must use them to answer relevant questions.\n"
    "Available tools:\n"
    "- get_weather(latitude, longitude): Get current weather for given coordinates.\n"
    "- book_recs(topic): Get book recommendations for a topic.\n"
    "- random_joke(): Tell a random joke.\n"
    "- random_dog(): Show a random dog image.\n"
    "- trivia(): Give a trivia question.\n"
    "\n"
    "When a user asks something that matches a tool, always call the tool.\n"
    "If you need a tool, output ONLY valid JSON: {\"action\":\"tool_name\",\"args\":{...}}\n"
    "If you are ready to answer, output ONLY: {\"action\":\"final\",\"answer\":\"...\"}\n"
    "Be explicit and do not answer from your own knowledge if a tool is available."
)

def llm_json(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    resp = chat(model="mistral:7b", messages=messages, options={"temperature": 0.2})
    txt = resp["message"]["content"]
    try:
        return json.loads(txt)
    except Exception as e:
        print("[DEBUG] LLM did not return valid JSON. Raw output:")
        print(txt)
        # force JSON if model drifted
        fix = chat(model="mistral:7b",
                   messages=[{"role": "system", "content": "Return ONLY valid JSON."},
                             {"role": "user", "content": txt}],
                   options={"temperature": 0})
        try:
            return json.loads(fix["message"]["content"])
        except Exception as e2:
            print("[DEBUG] Second attempt also failed. Raw output:")
            print(fix["message"]["content"])
            raise e2

async def main():
    server_path = sys.argv[1] if len(sys.argv) > 1 else "server.py"
    exit_stack = AsyncExitStack()
    try:
        stdio = await exit_stack.enter_async_context(
            stdio_client(StdioServerParameters(command="python", args=[server_path]))
        )
        r_in, w_out = stdio
        session = await exit_stack.enter_async_context(ClientSession(r_in, w_out))
        await session.initialize()

        tools = (await session.list_tools()).tools
        tool_index = {t.name: t for t in tools}
        print("Connected tools:", list(tool_index.keys()))

        history = [{"role": "system", "content": SYSTEM}]
        while True:
            user = input("You: ").strip()
            if not user or user.lower() in {"exit", "quit"}:
                break
            history.append({"role": "user", "content": user})

            for _ in range(4):  # small safety loop
                decision = llm_json(history)
                if decision.get("action") == "final":
                    answer = decision.get("answer", "")
                    # one-shot reflection
                    reflect = chat(
                        model="mistral:7b",
                        messages=[
                            {"role": "system", "content": "Check for mistakes or missing tool calls. If fine, reply 'looks good'; else give corrected answer."},
                            {"role": "user", "content": answer}
                        ],
                        options={"temperature": 0}
                    )
                    if reflect["message"]["content"].strip().lower() != "looks good":
                        answer = reflect["message"]["content"]
                    print("Agent:", answer)
                    history.append({"role": "assistant", "content": answer})
                    break

                tname = decision.get("action")
                args = decision.get("args", {})
                if tname not in tool_index:
                    history.append({"role": "assistant", "content": f"(unknown tool {tname})"})
                    continue

                result = await session.call_tool(tname, args)
                payload = result.content[0].text if result.content else result.model_dump_json()
                history.append({"role": "assistant", "content": f"[tool:{tname}] {payload}"})
    except Exception:
        pass
    finally:
        await exit_stack.aclose()
    server_path = sys.argv[1] if len(sys.argv) > 1 else "server.py"
    exit_stack = AsyncExitStack()
    try:
        stdio = await exit_stack.enter_async_context(
            stdio_client(StdioServerParameters(command="python", args=[server_path]))
        )
        r_in, w_out = stdio
        session = await exit_stack.enter_async_context(ClientSession(r_in, w_out))
        await session.initialize()

        tools = (await session.list_tools()).tools
        tool_index = {t.name: t for t in tools}
        print("Connected tools:", list(tool_index.keys()))

        history = [{"role": "system", "content": SYSTEM}]
        while True:
            user = input("You: ").strip()
            if not user or user.lower() in {"exit", "quit"}:
                break
            history.append({"role": "user", "content": user})

            for _ in range(4):  # small safety loop
                decision = llm_json(history)
                if decision.get("action") == "final":
                    answer = decision.get("answer", "")
                    # one-shot reflection
                    reflect = chat(
                        model="mistral:7b",
                        messages=[
                            {"role": "system", "content": "Check for mistakes or missing tool calls. If fine, reply 'looks good'; else give corrected answer."},
                            {"role": "user", "content": answer}
                        ],
                        options={"temperature": 0}
                    )
                    if reflect["message"]["content"].strip().lower() != "looks good":
                        answer = reflect["message"]["content"]
                    print("Agent:", answer)
                    history.append({"role": "assistant", "content": answer})
                    break

                tname = decision.get("action")
                args = decision.get("args", {})
                if tname not in tool_index:
                    history.append({"role": "assistant", "content": f"(unknown tool {tname})"})
                    continue

                result = await session.call_tool(tname, args)
                payload = result.content[0].text if result.content else result.model_dump_json()
                history.append({"role": "assistant", "content": f"[tool:{tname}] {payload}"})
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await exit_stack.aclose()

if __name__ == "__main__":
    asyncio.run(main())