from flask import Flask, request
import base64
import json
import agent as sre_agent_module # Import our agent.py
import os
import threading

app = Flask(__name__)

# 1. Unpack both the agent AND the instructions
sre_agent, agent_instructions = sre_agent_module.create_sre_agent() 

@app.route('/', methods=['POST'])
def handle_incident():
    envelope = request.get_json()
    
    if not envelope or 'message' not in envelope:
        print("Invalid Pub/Sub message format")
        return "Bad Request: Invalid Pub/Sub message", 400

    try:
        # 2. Parse the Pub/Sub message
        message_data = base64.b64decode(envelope['message']['data']).decode('utf-8')
        alert_json = json.loads(message_data)
        
        print(f"Received alert JSON: {json.dumps(alert_json, indent=2)}")

        # 3. Create the prompt for the agent
        incident = alert_json.get("incident", {})
        summary = incident.get("summary", "No summary")
        
        resource_name = "Unknown resource"
        resource_labels = incident.get("resource", {}).get("labels", {})
        if "service_name" in resource_labels:
            resource_name = resource_labels["service_name"]
        else:
            resource_name = incident.get("resource_name", "Unknown resource")

        # 4. Combine the instructions and the specific incident details
        full_prompt = f"""
        {agent_instructions}

        A new incident has fired:
        - Summary: {summary}
        - Resource Name: {resource_name}
        - Full Alert Payload: {json.dumps(incident)}

        Please begin your investigation.
        """

        # 5. Run the agent in a separate thread
        def run_agent_work():
            print(f"Starting agent chat with prompt: {full_prompt}")
            try:
                # 6. Pass the full, combined prompt to chat()
                for event in sre_agent.chat(full_prompt):
                    print(f"Agent Event: {event.type}")
                    if event.type == "tool_call":
                        print(f"Agent is calling tool: {event.tool_call.name} with args: {event.tool_call.args}")
                    if event.type == "tool_output":
                        print(f"Agent got tool output: {event.tool_output.output}")

            except Exception as e:
                print(f"Error during agent execution: {e}")

        # Start the agent work in a background thread
        thread = threading.Thread(target=run_agent_work)
        thread.start()

        # 7. Acknowledge the Pub/Sub message immediately
        print("Acknowledging Pub/Sub message.")
        return "OK", 204

    except Exception as e:
        print(f"Error processing request: {e}")
        return "Error", 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))