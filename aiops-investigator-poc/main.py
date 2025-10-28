from google.adk.agent import Agent
from google.adk.orchestration import langgraph
import graph
import tools

# Create the Investigator "Brain" Agent
investigator = Agent(
    orchestrator=langgraph.LangGraphOrchestrator(
        graph.AgentState
    )
)

# Register the tool that calls the remote MCP
investigator.register_tool(tools.call_mcp_hello_world)

# This 'agent' variable is what 'adk web' will run
agent = investigator