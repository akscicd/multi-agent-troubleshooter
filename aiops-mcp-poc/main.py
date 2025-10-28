from google.adk.agent import Agent
import tools

# The ADK agent for our MCP "Hands" server
agent = Agent()
agent.register_tool(tools.hello_world)

# This 'app' variable is what Gunicorn will run
app = agent.get_flask_app()