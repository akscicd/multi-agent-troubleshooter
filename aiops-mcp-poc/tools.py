from google.adk.tools import FunctionTool

@FunctionTool
def hello_world(name: str) -> str:
  """
  A simple test tool that returns a greeting.
  Use this to say hello to someone.
  Args:
    name: The name of the person to greet.
  Returns:
    A greeting string.
  """
  # This print statement will show up in the "Hands" terminal
  print(f"MCP 'Hands' Server: 'hello_world' tool was called with name: {name}")
  return f"Hello, {name}. This message came from the MCP 'Hands' service!"