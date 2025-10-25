import datetime
from google.adk.tools import FunctionTool
from google.cloud import logging_v2
from google.cloud import monitoring_v3
from google.cloud import run_v2
from google.protobuf.timestamp_pb2 import Timestamp

# --- CONFIGURATION ---
# TODO: Change these to your project's values
PROJECT_ID = "global-admin-472117" 
REGION = "us-central1" # The region your Cloud Run services are in
# ---------------------

@FunctionTool
def get_gcp_logs(resource_name: str, time_window_minutes: int) -> str:
    """
    Fetches ERROR logs for a given Cloud Run service in the last N minutes.
    Use this to find error messages and root causes.
    `resource_name` should be the short service name (e.g., 'victim-app').
    """
    print(f"Tool: Getting logs for {resource_name}...")
    client = logging_v2.LoggingServiceV2Client()
    
    end_time = datetime.datetime.now(datetime.timezone.utc)
    start_time = end_time - datetime.timedelta(minutes=time_window_minutes)

    # Format timestamps for the API
    end_time_str = end_time.isoformat()
    start_time_str = start_time.isoformat()

    filter_str = f"""
    resource.type="cloud_run_revision"
    resource.labels.service_name="{resource_name}"
    severity="ERROR"
    timestamp >= "{start_time_str}"
    timestamp <= "{end_time_str}"
    """

    request = logging_v2.ListLogEntriesRequest(
        resource_names=[f"projects/{PROJECT_ID}"],
        filter=filter_str,
        order_by="timestamp desc",
        page_size=10, # Get the 10 most recent error logs
    )

    try:
        entries = client.list_log_entries(request=request)
        log_entries_str = "Found logs:\n"
        for entry in entries:
            log_time = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            message = entry.text_payload or entry.json_payload or "No log payload"
            log_entries_str += f"- {log_time} UTC: {message}\n"
        
        if not entries:
            return "No ERROR logs found in the time window."
            
        return log_entries_str
    except Exception as e:
        print(f"Error in get_gcp_logs: {e}")
        return f"Error fetching logs: {e}"

@FunctionTool
def get_gcp_metrics(resource_name: str, metric_type: str, time_window_minutes: int) -> str:
    """
    Fetches a specific metric (e.g., 'run.googleapis.com/request_count')
    for a resource in the last N minutes. Use this to check for spikes.
    `resource_name` should be the short service name (e.g., 'victim-app').
    """
    print(f"Tool: Getting metrics for {resource_name}...")
    client = monitoring_v3.MetricServiceClient()
    
    end_time = Timestamp()
    end_time.FromDatetime(datetime.datetime.now(datetime.timezone.utc))
    start_time = Timestamp()
    start_time.FromDatetime(end_time.ToDatetime() - datetime.timedelta(minutes=time_window_minutes))

    interval = monitoring_v3.TimeInterval(
        start_time=start_time, end_time=end_time
    )

    # Example metric_type: 'run.googleapis.com/request_count'
    request = monitoring_v3.ListTimeSeriesRequest(
        name=f"projects/{PROJECT_ID}",
        filter=f'metric.type = "{metric_type}" AND resource.labels.service_name = "{resource_name}"',
        interval=interval,
        view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
    )

    try:
        results = client.list_time_series(request=request)
        metrics_str = f"Metric data for {metric_type} on {resource_name}:\n"
        
        for result in results:
            for point in result.points:
                value_type = point.value.WhichOneof("value")
                value = getattr(point.value, value_type)
                metrics_str += f"- At {point.interval.start_time.ToDatetime()}: {value}\n"
        
        if not results:
            return "No metric data found for this filter."

        return metrics_str
    except Exception as e:
        print(f"Error in get_gcp_metrics: {e}")
        return f"Error fetching metrics: {e}"

@FunctionTool
def get_cloud_run_revisions(service_name: str) -> str:
    """
    Gets the list of deployed revisions for a Cloud Run service and their traffic split.
    Use this to find the 'last known good' revision.
    `service_name` should be the short service name (e.g., 'victim-app').
    """
    print(f"Tool: Getting revisions for {service_name}...")
    client = run_v2.RevisionsClient()
    service_parent = f"projects/{PROJECT_ID}/locations/{REGION}/services/{service_name}"

    request = run_v2.ListRevisionsRequest(
        parent=service_parent,
    )

    try:
        # Get traffic split from the Service first
        service_client = run_v2.ServicesClient()
        service_info = service_client.get_service(name=service_parent)
        traffic_map = {split.revision: split.percent for split in service_info.traffic}

        # List the revisions
        revisions = client.list_revisions(request=request)
        revisions_str = "Found revisions:\n"
        
        for rev in revisions:
            rev_name_short = rev.name.split('/')[-1] # Get just the 'victim-app-00001-abc' part
            traffic_percent = traffic_map.get(rev.name, 0)
            created_time = rev.create_time.strftime('%Y-%m-%d %H:%M:%S')
            revisions_str += f"- {rev_name_short} (traffic: {traffic_percent}%), Created: {created_time} UTC\n"

        return revisions_str
    except Exception as e:
        print(f"Error in get_cloud_run_revisions: {e}")
        return f"Error fetching revisions: {e}"
