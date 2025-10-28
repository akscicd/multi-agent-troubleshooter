import httpx
from google.adk.tools import FunctionTool

# This is the key: we point to the local "Hands" server's address
MCP_SERVICE_URL = "http://localhost:8000"

@FunctionTool
def call_mcp_hello_world(name: str) -> str:
  """
  Contacts the remote MCP (Master Control Program) server to get a greeting.
  Use this tool when you need to say hello to someone.
  Args:
    name: The name of the person to greet.
  Returns:
    The response from the MCP server.
  """
  try:
    endpoint = "/hello_world"
    url = f"{MCP_SERVICE_URL}{endpoint}"
    payload = {"name": name}

    # This print statement will show up in the "Brain" terminal
    print(f"Investigator 'Brain': Calling MCP at {url}...")

    response = httpx.post(url, json=payload, timeout=30)
    response.raise_for_status() 

    result = response.json().get("output")
    print(f"Investigator 'Brain': Received response: {result}")
    return result

  except httpx.RequestError as e:
    error_message = f"ERROR: Could not connect to MCP at {url}. Is the 'Hands' server running in the other terminal?"
    print(error_message)
    return error_message