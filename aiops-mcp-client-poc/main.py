from google.adk.agent import Agent

# In a real app, this URL would be in a config file
# For this POC, we're hardcoding it
hands_url = "http://127.0.0.1:8000/process_message"

# The ADK agent for our MCP "Brains" server
agent = Agent()
agent.add_tool_server_config(url=hands_url)

# This is our main interactive loop for the "Brains"
if __name__ == "__main__":
  # This print statement will show up in the "Brains" terminal
  print("MCP 'Brains' Client: Sending a message to the 'Hands' server...")
  response = agent.send_message("Can you say hello to the world for me?")
  # This print statement will show up in the "Brains" terminal
  print(f"MCP 'Brains' Client: Received response: '{response.get_text()}'")