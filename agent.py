from google.adk import Agent
from tools import gcp_observe, slack # Import our tool files
from tools.gcp_observe import FunctionTool # We need this import
from tools.slack import FunctionTool # We need this import

# Define the high-level prompt
AGENT_INSTRUCTIONS = """
You are a Google Cloud SRE Agent. Your goal is to troubleshoot live production incidents.
An incident alert will be provided by the user.

Your process is:
1.  Analyze the alert. The resource name will be in the `resource_name` field.
2.  Use your tools to gather context. First, get logs. Then, get metrics like 'run.googleapis.com/request_count' for the service.
3.  After logs and metrics, get the list of Cloud Run revisions.
4.  Formulate a root cause hypothesis based on all data.
5.  Formulate a single, executable `gcloud` command to mitigate the issue. 
    - A common mitigation is rolling back to a previous revision.
    - The command for that is: `gcloud run services update-traffic {service_name} --to-revisions={revision_name}=100 --region={region}`
    - Example: `gcloud run services update-traffic victim-app --to-revisions=victim-app-00001-abc=100 --region=us-central1`
6.  Call the `send_plan_for_approval` tool with your hypothesis and the command.

Do NOT run the `gcloud` command yourself. A human MUST approve it.
"""

def create_sre_agent():
    # The ADK automatically finds all @FunctionTool-decorated functions
    agent = Agent(
        name="sre_agent",  # <--- 1. ADDED THIS REQUIRED FIELD
        # instructions=AGENT_INSTRUCTIONS, # <-- 2. REMOVED THIS FORBIDDEN FIELD
        tools=[
            gcp_observe.get_gcp_logs,
            gcp_observe.get_gcp_metrics,
            gcp_observe.get_cloud_run_revisions,
            slack.send_plan_for_approval,
        ],
        model="gemini-1.5-pro-latest" # Use a powerful model
    )
    # 3. Return both the agent AND the instructions
    return agent, AGENT_INSTRUCTIONS