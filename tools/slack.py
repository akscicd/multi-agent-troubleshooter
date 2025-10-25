from google.adk.tools import FunctionTool
from google.cloud import secretmanager
import requests
import json

# --- CONFIGURATION ---
PROJECT_ID = "global-admin-472117"  # Change this
SLACK_WEBHOOK_SECRET_NAME = "slack-webhook-url"
# This will be filled in Phase 4/5
EXECUTOR_URL = "URL_of_your_sre-agent-executor_service" 
# ---------------------

def get_slack_webhook_url():
    """Fetches the Slack webhook URL from Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{PROJECT_ID}/secrets/{SLACK_WEBHOOK_SECRET_NAME}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Failed to get secret: {e}")
        return None

@FunctionTool
def send_plan_for_approval(hypothesis: str, gcloud_command: str):
    """
    Call this tool ONLY AFTER you have a hypothesis AND a gcloud command.
    This sends the plan to a human SRE in Slack for approval.
    """
    print(f"Tool: Sending plan to Slack: {gcloud_command}")
    
    SLACK_WEBHOOK_URL = get_slack_webhook_url()
    if not SLACK_WEBHOOK_URL:
        return "Error: Could not retrieve Slack Webhook URL from Secret Manager."

    # This is Slack's "Block Kit" format for rich messages
    slack_message = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🔥 SRE Agent - Approval Required"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*AI Hypothesis:*\n{hypothesis}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Proposed Fix:*\n```{gcloud_command}```"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ Approve & Run",
                            "emoji": True
                        },
                        "style": "primary", # Makes the button green
                        "url": f"{EXECUTOR_URL}?command={gcloud_command}",
                        "action_id": "approve_button" 
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(SLACK_WEBHOOK_URL, data=json.dumps(slack_message))
        response.raise_for_status() # Raise an exception for bad status codes
        return "Plan sent to SREs in Slack for approval."
    except requests.exceptions.RequestException as e:
        print(f"Error sending to Slack: {e} - {e.response.text}")
        return f"Error sending to Slack: {e.response.text}"