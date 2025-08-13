from agents import Agent, Runner, set_tracing_disabled, trace, function_tool
from agents import ModelSettings
import asyncio
from openai.types.responses import ResponseTextDeltaEvent
from dotenv import load_dotenv
import os
load_dotenv()
    
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY")
    
print(f"OpenAI API Key set: {'Yes' if os.environ.get('OPENAI_API_KEY') and os.environ['OPENAI_API_KEY'] != 'YOUR_OPENAI_API_KEY' else 'No (REPLACE PLACEHOLDER!)'}")
print(f"Google API Key set: {'Yes' if os.environ.get('GOOGLE_API_KEY') and os.environ['GOOGLE_API_KEY'] != 'YOUR_GOOGLE_API_KEY' else 'No (REPLACE PLACEHOLDER!)'}")
# disable tracing


@function_tool
def get_weather(city: str) -> str:
    return f"The weather in {city} is sunny."


function_agent = Agent(
    name="Function Agent",
    instructions="You are a helpful agent.",
    tools=[get_weather],
)

advanced_agent = Agent(
   name="Advanced Assistant",
   instructions="""You are a an advnanced assistant who knows about engineering facts. Give 
   accurate information. If you don't know something, clearly state that.
   Take a pass if you don't know. """,
   model="gpt-4o",
   model_settings=ModelSettings(
       temperature=0.3,  # Lower for more deterministic outputs (0.0-2.0)
       max_tokens=1024,  # Maximum length of response
   ),
   tools=[]  # We'll cover tools in a later section
)

history_agent = Agent(
    name="History Tutor",
    handoff_description="Specialist agent for historical questions",
    instructions="You provide assistance with historical queries. Explain important events and context clearly.",
)

math_agent = Agent(
    name="Math Tutor",
    instructions="You provide help with math problems. Explain your reasoning at each step and include examples",
    model="gpt-4o"
)

joker_agent = Agent(
        name="Joker",
        instructions="You are a helpful assistant.",
)

french_agent = Agent(
    name="french agent",
    instructions="You only speak French.",
)

italian_agent = Agent(
    name="italian agent",
    instructions="You only speak Italian.",
)

spanish_agent = Agent(
    name="Spanish agent",
    instructions="You only speak Spanish.",
)

english_agent = Agent(
    name="English agent",
    instructions="You only speak English",
)

triage_agent = Agent(
    name="Triage agent",
    instructions="Handoff to the appropriate agent based on the language of the request.",
    handoffs=[spanish_agent, english_agent, french_agent, italian_agent],
)

triage_hw_agent = Agent(
    name="Triage HW Agent",
    instructions="You determine which agent to use based on the user's homework question",
    handoffs=[history_agent, math_agent]
)

async def run_math_agent():
    result = Runner.run_streamed(math_agent, input="what is square root of 4.")
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)

    result = Runner.run_streamed(joker_agent, input="Please tell me 5 jokes.")
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)


    result = await Runner.run(math_agent, "what is square root of 9")
    print(result.final_output)

    result = await Runner.run(advanced_agent, "Tell me about quantum computers.")
    print(result.final_output)

    input="Hola, ¿cómo estás?"
    result = await Runner.run(triage_agent, input=input)
    print(f" Input = {input}, Output = {result.final_output}")
    input="Hello How are you?"
    result = await Runner.run(triage_agent, input=input)
    print(f" Input = {input}, Output = {result.final_output}")
    input="bonjour comment allez-vous?"
    result = await Runner.run(triage_agent, input=input )
    print(f" Input = {input}, Output = {result.final_output}")
    input="Salve, come stai?"
    result = await Runner.run(triage_agent, input=input)
    print(f" Input = {input}, Output = {result.final_output}")
    #print(result.final_output)
    # ¡Hola! Estoy bien, gracias por preguntar. ¿Y tú, cómo estás?

    result = await Runner.run(triage_hw_agent, input="Where is 2028 olympics?")
    print(result.final_output)
    result = await Runner.run(triage_hw_agent, input="What is 0 + 1?")
    print(result.final_output)
    result = await Runner.run(triage_hw_agent, "What is the capital of France?")
    print(result.final_output)

    result = await Runner.run(function_agent, input="What's the weather in Tokyo?")
    print(result.final_output)

async def main():
    agent = Agent(name="Assistant", 
                  instructions="Reply very concisely.",
                  model="gpt-5")
    thread_id = "1234"
    with trace(workflow_name="Conversation", group_id=thread_id):
        # First turn
        result = await Runner.run(agent, "What city is the Golden Gate Bridge in?")
        print(result.final_output)
        # San Francisco

        # Second turn
        new_input = result.to_input_list() + [{"role": "user", "content": "What state is it in?"}]
        result = await Runner.run(agent, new_input)
        print(result.final_output)
        # California
        await run_math_agent()
if __name__ == "__main__":
    asyncio.run(main())
    
