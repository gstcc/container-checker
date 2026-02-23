import docker
import time
import json
from datetime import datetime
from colorama import init, Fore, Style, Back
from pathlib import Path

# Initialize colorama for cross-platform colored output
init(autoreset=True)

class DockerHealthMonitor:
    """Monitor Docker container health and send local notifications."""

    def __init__(self, check_interval=10, log_dir="logs"):
        """Initialize the monitor."""
        self.client = docker.from_env()
        self.check_interval = check_interval
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.container_states = {}

        # Log files
        self.alert_log = self.log_dir / "alerts.log"
        self.health_log = self.log_dir / "health_status.json"

    def get_container_health(self, container):
        container.reload()
        health_info = {
            "name": container.name,
            "id": container.short_id,
            "status": container.status,
            "health": "none",
            "timestamp": datetime.now().isoformat()
        }

        # Check if container has health check configured
        if container.attrs.get("State", {}).get("Health"):
            health_status = container.attrs["State"]["Health"]["Status"]
            health_info["health"] = health_status

            # Get the last health check log
            health_logs = container.attrs["State"]["Health"].get("Log", [])
            if health_logs:
                last_log = health_logs[-1]
                health_info["last_check_output"] = last_log.get("Output", "")
                health_info["last_check_exit_code"] = last_log.get("ExitCode", 0)

        return health_info
