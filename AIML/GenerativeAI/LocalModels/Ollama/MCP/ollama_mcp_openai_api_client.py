import asyncio
#import markdown
import json
import sys
from typing import Optional
from contextlib import AsyncExitStack
#from rich import print

import openai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from ollama import Client, AsyncClient
from openai import OpenAI


import os
from dotenv import load_dotenv
  
# 1. Load environment variables from the .env file
load_dotenv()
  
# 2. Get the API key from the environment variable
api_key = os.getenv("OLLAMA_API_KEY")

# Check if the API key was loaded successfully
if not api_key:
    raise ValueError("OLLAMA_API_KEY not found in .env file.")
  
#client = Client(
#  #host="https://ollama.com", headers={'Authorization': api_key}
#)


client = OpenAI(
    base_url = 'http://localhost:11434/v1',
    api_key='ollama', # required, but unused
)

model_name='gpt-oss:20b'

class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_server(self, server_script_path: str):
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(command=command, args=[server_script_path])
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()

        response = await self.session.list_tools()
        tools = response.tools
        print("\n✅ Connected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        messages = [{"role": "user", "content": query}]

        response = await self.session.list_tools()
        available_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            }
        } for tool in response.tools]

        # Initial OpenAI API call
        response = client.chat.completions.create(
            model=model_name,
            max_tokens=1000,
            messages=messages,
            tools=available_tools
        )


        # Process response and handle tool calls
        tool_results = []
        final_text = [] 
        
        message = response.choices[0].message

        # Check if there's text content
        if message.content:
            final_text.append(message.content)

        # Check for tool calls
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)  # Parse JSON string to dict

                # Execute tool call
                result = await self.session.call_tool(tool_name, tool_args)
                tool_results.append({"call": tool_name, "result": result})
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                # Add tool result to conversation
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tool_call]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result.content)
                })

                # Get next response from OpenAI
                response = client.chat.completions.create(
                    model=model_name,
                    max_tokens=1000,
                    messages=messages,
                )

                final_text.append(response.choices[0].message.content)

        return "\n".join(final_text)


    async def chat_loop(self):
        print("\n🧠 MCP Ollama Client Started! Type your queries or 'quit' to exit.")
        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == 'quit':
                    break
                response = await self.process_query(query)
                print("\n" + response)
                #print(markdown.markdown(response))
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")

    async def cleanup(self):
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python ollama_client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())


