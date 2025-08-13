import asyncio
from agents import Agent, FileSearchTool, Runner, WebSearchTool, function_tool
from agents import Agent, ItemHelpers, MessageOutputItem, Runner, trace
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import os
load_dotenv()

OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")


"""
This example shows the agents-as-tools pattern. The frontline agent receives a user message and
then picks which agents to call, as tools. In this case, it picks from a set of translation
agents. It can also search web for you.
"""

malayalam_agent = Agent(
    name="malayalam_agent",
    instructions="You translate the user's message to Malayalam",
    handoff_description="An english to Malaylam translator",
)

spanish_agent = Agent(
    name="spanish_agent",
    instructions="You translate the user's message to Spanish",
    handoff_description="An english to spanish translator",
)

french_agent = Agent(
    name="french_agent",
    instructions="You translate the user's message to French",
    handoff_description="An english to french translator",
)

italian_agent = Agent(
    name="italian_agent",
    instructions="You translate the user's message to Italian",
    handoff_description="An english to italian translator",
)
websearch_agent = Agent(
    name="websearch_agent",
    instructions=f"You are a helpful agent who can search web, respond to questions by using the search tool",
    model="gpt-4o",
    tools=[WebSearchTool()]
)

orchestrator_agent = Agent(
    name="orchestrator_agent",
    instructions=(
        "You are a translation agent. You use the tools given to you to translate."
        "If asked for multiple translations, you call the relevant tools in order."
        "You never translate on your own, you always use the provided tools."
    ),
    tools=[
        malayalam_agent.as_tool(
            tool_name="translate_to_malaylam",
            tool_description="Translate the user's message to Malayalam",
        ),
        spanish_agent.as_tool(
            tool_name="translate_to_spanish",
            tool_description="Translate the user's message to Spanish",
        ),
        french_agent.as_tool(
            tool_name="translate_to_french",
            tool_description="Translate the user's message to French",
        ),
        italian_agent.as_tool(
            tool_name="translate_to_italian",
            tool_description="Translate the user's message to Italian",
        ),
        websearch_agent.as_tool(
            tool_name="websearch_agent",
            tool_description="search web to find answers to user query",
        ),

    ],
)

synthesizer_agent = Agent(
    name="synthesizer_agent",
    instructions="You inspect translations, correct them if needed, and produce a final concatenated response.",
)


async def main():
    print("\nI can translate to Malayalm, Spanish, French or Italian or do a web searc \n")
    msg = input("Hi! What would you like translated and to which languages or search web? ")

    # Run the entire orchestration in a single trace
    with trace("Orchestrator evaluator"):
        orchestrator_result = await Runner.run(orchestrator_agent, msg, max_turns=5,)
        for item in orchestrator_result.new_items:
            if hasattr(item, 'agent'):
               print(f" Agent: {item.agent.name}")
            if isinstance(item, MessageOutputItem):
                text = ItemHelpers.text_message_output(item)
                if text:
                    print(f"  - Translation step: {text}")

        synthesizer_result = await Runner.run(
            synthesizer_agent, orchestrator_result.to_input_list()
        )

    print(f"\n\nFinal response:\n{synthesizer_result.final_output}")
    

# async def main():
#     result = await Runner.run(orchestrator_agent, input="Say 'Hello, how are you?' in Spanish.")
#     print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
