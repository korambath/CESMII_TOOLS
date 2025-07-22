from agents import Agent, Runner
import os
from openai import OpenAI, OpenAIError
from pathlib import Path
from dotenv import load_dotenv
import logging

from agents import enable_verbose_stdout_logging

enable_verbose_stdout_logging()


load_dotenv()

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_APIUC_KEY"))


logger = logging.getLogger("openai.agents") # or openai.agents.tracing for the Tracing logger

# To make all logs show up
logger.setLevel(logging.DEBUG)
# To make info and above show up
logger.setLevel(logging.INFO)
# To make warning and above show up
logger.setLevel(logging.WARNING)
# etc

# You can customize this as needed, but this will output to `stderr` by default
logger.addHandler(logging.StreamHandler())


agent = Agent(name="TestAgent", instructions="Return 'Setup successful'")
result = Runner.run_sync(agent, "Run test")
print(result.final_output)
logger.info(result.final_output)
