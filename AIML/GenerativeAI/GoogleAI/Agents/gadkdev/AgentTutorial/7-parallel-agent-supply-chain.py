# @title Import necessary libraries
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools import google_search
from google.genai import types
from google import genai
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()


# The client gets the API key from the environment variable `GEMINI_API_KEY`.
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
      raise ValueError("GOOGLE_API_KEY environment variable not set.")
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
# --- Verify Keys (Optional Check) ---
print("API Keys Set:")
print(f"Google API Key set: {'Yes' if os.environ.get('GOOGLE_API_KEY') and os.environ['GOOGLE_API_KEY'] != 'YOUR_GOOGLE_API_KEY' else 'No (REPLACE PLACEHOLDER!)'}")

# Configuration
class SupplyChainConfig:
    def __init__(self):
        self.app_name = "parallel_research_app"
        self.user_id = "research_user_01"
        self.session_id = "parallel_research_session"
        self.gemini_model = "gemini-2.5-flash"
        self.supplier_name = "Intel" # Apple, Samsung, NVIDIA
        self.region = "North America"
        self.location = "California"

config = SupplyChainConfig()

def create_supply_agent(agent_name: str, model_name: str, specialization: str, supplier_name: str, topic: str, region: str, location: str, description: str, output_key: str) -> LlmAgent:
    """
    Create a specialized research agent for supply chain risk assessment.
    
    Args:
        agent_name: Name of the agent
        model_name: AI model to use
        specialization: Area of expertise (e.g., 'financial risk assessment')
        supplier_name: Name of the supplier to analyze
        topic: Specific topics to research
        region: Geographic region
        location: Specific location
        description: Agent description
        output_key: Key to store results in session state
        
    Returns:
        LlmAgent configured for the specified research area
    """
    researcher_agent = LlmAgent(
        name=agent_name,
        model=model_name,
        instruction=f"""You are an AI Research Assistant specializing in {specialization}.
        Evaluate the {specialization.lower()} for {supplier_name} in the region {region} and location {location}.
        Paths to consider:
        1. Check recent items related to {topic} etc.
        2. Look into overall reputation and compliance with regulations.

        Research the latest advancements in {topic}.
        Use the following format for reasoning:
        Thought: Define the specific {topic} aspects in the region {region} and {location} to examine.
        Use the Google Search tool provided.
        Observation: Analyze results.
        If concerning terms or negative indicators appear, conduct follow-up searches for recent developments.
        Summarize your key findings concisely (1-2 sentences).
        Output *only* the summary.
        """,
        description=description,
        tools=[google_search],
        # Store result in state for the merger agent
        output_key=output_key
    )
    return researcher_agent

def create_research_agents(config: SupplyChainConfig):
    """Factory function to create all research agents with consistent configuration."""
    
    # Financial Risk Agent
    financial_risk_agent = create_supply_agent(
        agent_name="FinancialRiskResearcher",
        model_name=config.gemini_model,
        specialization="financial risk assessment",
        supplier_name=config.supplier_name,
        topic="finance, profit, debt levels, loan, default, reputation",
        region=config.region,
        location=config.location,
        description=f"Financial risk for {config.supplier_name} in {config.region}, {config.location}",
        output_key="financial_risk_result"
    )
    
    # Geopolitical Risk Agent
    geopolitical_risk_agent = create_supply_agent(
        agent_name="GeoPoliticalRiskResearcher",
        model_name=config.gemini_model,
        specialization="Geopolitical risk assessment",
        supplier_name=config.supplier_name,
        topic="political unrest, sanctions, restructuring, loan, default, reputation",
        region=config.region,
        location=config.location,
        description=f"Geopolitical risk for {config.supplier_name} in {config.region}, {config.location}",
        output_key="geopolitical_risk_result"
    )
    
    # Environmental Risk Agent
    environmental_risk_agent = create_supply_agent(
        agent_name="EnvironmentalRiskResearcher",
        model_name=config.gemini_model,
        specialization="Environmental risk assessment",
        supplier_name=config.supplier_name,
        topic="natural disasters, government policy adaptation, incentives",
        region=config.region,
        location=config.location,
        description=f"Environmental risk for {config.supplier_name} in {config.region}, {config.location}",
        output_key="environmental_risk_result"
    )
    
    return financial_risk_agent, geopolitical_risk_agent, environmental_risk_agent


# Create research agents
financial_risk_agent, geopolitical_risk_agent, environmental_risk_agent = create_research_agents(config)

 # --- 2. Create the ParallelAgent (Runs researchers concurrently) ---
 # This agent orchestrates the concurrent execution of the researchers.
 # It finishes once all researchers have completed and stored their results in state.
parallel_research_agent = ParallelAgent(
     name="ParallelWebResearchAgent",
     sub_agents=[financial_risk_agent, geopolitical_risk_agent, environmental_risk_agent],
     description="Runs multiple research agents in parallel to gather information."
)

 # --- 3. Define the Merger Agent (Runs *after* the parallel agents) ---
 # This agent takes the results stored in the session state by the parallel agents
 # and synthesizes them into a single, structured response with attributions.
merger_agent = LlmAgent(
     name="SynthesisAgent",
     model=config.gemini_model,  # Or potentially a more powerful model if needed for synthesis
     instruction="""You are an AI Assistant responsible for combining research findings into a structured report.

 Your primary task is to synthesize the following research summaries, clearly attributing findings to their source areas. Structure your response using headings for each topic. Ensure the report is coherent and integrates the key points smoothly.

 **Crucially: Your entire response MUST be grounded *exclusively* on the information provided in the 'Input Summaries' below. Do NOT add any external knowledge, facts, or details not present in these specific summaries.**

 **Input Summaries:**

 *   **Financial Risk:**
     {financial_risk_result}

 *   **Geopolitical Risk:**
     {geopolitical_risk_result}

 *   **Environmental Risk:**
     {environmental_risk_result}

 **Output Format:**

 ## Summary of Recent Risk Assessments

 ### Financial Risk Findings
 (Based on Financial risk Researcher's findings)
 [Synthesize and elaborate *only* on the financial risk input summary provided above.]

 ### Geo Political Findings
 (Based on geopolitical reserarcher's findings)
 [Synthesize and elaborate *only* on the geopolitical input summary provided above.]

 ### Environmental Risk Findings
 (Based on Environmental Risk Researcher's findings)
 [Synthesize and elaborate *only* on the enviromental risk input summary provided above.]

 ### Overall Conclusion
 [Provide a brief (1-2 sentence) concluding statement that connects *only* the findings presented above.]

 Output *only* the structured report following this format. Do not include introductory or concluding phrases outside this structure, and strictly adhere to using only the provided input summary content.
 """,
     description="Combines research findings from parallel agents into a structured, cited report, strictly grounded on provided inputs.",
     # No tools needed for merging
     # No output_key needed here, as its direct response is the final output of the sequence
)


 # --- 4. Create the SequentialAgent (Orchestrates the overall flow) ---
 # This is the main agent that will be run. It first executes the ParallelAgent
 # to populate the state, and then executes the MergerAgent to produce the final output.
sequential_pipeline_agent = SequentialAgent(
     name="ResearchAndSynthesisPipeline",
     # Run parallel research first, then merge
     sub_agents=[parallel_research_agent, merger_agent],
     description="Coordinates parallel research and synthesizes the results."
)

root_agent = sequential_pipeline_agent

async def create_and_manage_session(app_name, user_id, session_id, query):
    """Create session and run the agent pipeline with the given query."""
    session_service = None
    runner = None
    
    try:
        session_service = InMemorySessionService()
        session = await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
        print("Session created successfully")
        
        runner = Runner(agent=root_agent, app_name=app_name, session_service=session_service)
        
        # Run the agent with the query
        content = types.Content(role='user', parts=[types.Part(text=query)])
        events = runner.run(user_id=user_id, session_id=session_id, new_message=content)
        
        print("Processing agent response...")
        final_response = None
        #for event in events: 
        #    if event.is_final_response():
        #        final_response = event.content.parts[0].text
        #        print("Agent Response: ", final_response)

        
        # Collect all events to ensure proper completion
        event_list = list(events)
        for event in event_list:
            if event.is_final_response():
                final_response = event.content.parts[0].text
                #print(f"Agent Response for {event}: \n")
                print(f"Agent Response for : \n")
                print(final_response)
                #break
        
        if not final_response:
            print("No final response received from agent")
            
        # Add a small delay to allow background threads to complete
        await asyncio.sleep(0.1)
        
        return final_response
        
    except Exception as e:
        print(f"Error during session execution: {str(e)}")
        return None
    
    finally:
        # Cleanup resources
        if session_service:
            try:
                # Give time for any pending operations to complete
                await asyncio.sleep(0.05)
            except Exception:
                pass

if __name__ == "__main__":
    query = "research latest trends for Intel supply chain risks"
    print("Starting parallel supply chain risk analysis...")
    
    try:
        result = asyncio.run(create_and_manage_session(
            config.app_name, 
            config.user_id, 
            config.session_id, 
            query
        ))
        
        if result:
            print("Analysis completed successfully")
        else:
            print("Analysis failed to complete")
            
    except KeyboardInterrupt:
        print("Analysis interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    finally:
        # Give asyncio time to clean up background tasks
        try:
            import time
            time.sleep(0.1)
        except Exception:
            pass
