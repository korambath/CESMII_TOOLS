from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio
import os

os.environ["USER_AGENT"] = "my-langchain-agent/1.0"  # Optional but clean


OLLAMA_MODEL="gpt-oss"
OLLAMA_MODEL="llama3.2"

async def main():

  client = MultiServerMCPClient({
    "math": {
        "command": "python",
        "args": ["mcp_math_server.py"],
        "transport": "stdio",
      }
    })

        # Get tools
  tools = await client.get_tools()
  llm = ChatOllama(
       model=OLLAMA_MODEL,
       temperature=0,
    # other params...
  )

  # Create proper prompt template for tool calling agent
  prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant with access to tools from an mcp server. Use the tools to answer queries. Do not correct answers from the tools"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
      ])


  agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
 
    # The AgentExecutor is responsible for running the agent with the provided tools.
  agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=False
  )

    # Now we can use the agent to answer questions.
  input_message="What's 5 + 3, then multiply by 2, and then divide by 4?"
  #input_message="What's weather in Los Angeles, CA?"
  print(f"Input is {input_message}")
  result = await agent_executor.ainvoke({"input": input_message})
  print(f"\nResult: {result}")
  print(result["output"])

if __name__ == "__main__":
        asyncio.run(main())
