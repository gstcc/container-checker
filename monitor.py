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

    def send_alert(self, container_info, alert_type="UNHEALTHY"):
        """Send a local alert about container health issue."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        container_name = container_info["name"]

        # Color-coded console output
        if alert_type == "UNHEALTHY":
            print(f"{Fore.RED}{Back.WHITE}{Style.BRIGHT} ⚠ ALERT {Style.RESET_ALL} "
                  f"{Fore.RED}{container_name}{Style.RESET_ALL} is {Fore.RED}UNHEALTHY{Style.RESET_ALL}")
        elif alert_type == "STOPPED":
            print(f"{Fore.YELLOW}{Back.BLACK}{Style.BRIGHT} ⚠ ALERT {Style.RESET_ALL} "
                  f"{Fore.YELLOW}{container_name}{Style.RESET_ALL} has {Fore.YELLOW}STOPPED{Style.RESET_ALL}")
        elif alert_type == "RECOVERED":
            print(f"{Fore.GREEN}{Back.WHITE}{Style.BRIGHT} ✓ RECOVERED {Style.RESET_ALL} "
                  f"{Fore.GREEN}{container_name}{Style.RESET_ALL} is now {Fore.GREEN}HEALTHY{Style.RESET_ALL}")

        # Log to file
        with open(self.alert_log, "a") as f:
            f.write(f"[{timestamp}] {alert_type}: {container_name}\n")
            f.write(f"  Details: {json.dumps(container_info, indent=2)}\n")
            f.write("-" * 80 + "\n")

        # Create notification file for external monitoring
        notification_file = self.log_dir / "latest_alert.txt"
        with open(notification_file, "w") as f:
            f.write(f"{alert_type}: {container_name}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")


    def check_containers(self):
        """Check all containers and detect health issues."""
        try:
            containers = self.client.containers.list(all=True)

            if not containers:
                print(f"{Fore.CYAN}No containers found to monitor.{Style.RESET_ALL}")
                return

            current_states = {}

            for container in containers:
                health_info = self.get_container_health(container)
                container_name = health_info["name"]
                current_states[container_name] = health_info

                # Get previous state
                previous_state = self.container_states.get(container_name, {})

                # Detect state changes and issues
                if health_info["health"] == "unhealthy":
                    if previous_state.get("health") != "unhealthy":
                        self.send_alert(health_info, "UNHEALTHY")

                elif health_info["status"] in ["exited", "dead", "stopped"]:
                    if previous_state.get("status") not in ["exited", "dead", "stopped"]:
                        self.send_alert(health_info, "STOPPED")

                elif health_info["health"] == "healthy":
                    # Check if recovered from unhealthy state
                    if previous_state.get("health") == "unhealthy":
                        self.send_alert(health_info, "RECOVERED")

            # Update container states
            self.container_states = current_states

            # Save current state to JSON file
            with open(self.health_log, "w") as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "containers": current_states
                }, f, indent=2)

        except docker.errors.DockerException as e:
            print(f"{Fore.RED}Docker error: {e}{Style.RESET_ALL}")


    def print_status_summary(self):
        """Print a summary of all container statuses."""
        if not self.container_states:
            return

        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}Container Health Status Summary{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'='*80}{Style.RESET_ALL}")

        for name, info in self.container_states.items():
            status = info["status"]
            health = info["health"]

            # Color code based on health
            if health == "healthy":
                status_color = Fore.GREEN
                symbol = "✓"
            elif health == "unhealthy":
                status_color = Fore.RED
                symbol = "✗"
            elif health == "starting":
                status_color = Fore.YELLOW
                symbol = "⟳"
            else:
                status_color = Fore.WHITE
                symbol = "○"

            print(f"{symbol} {status_color}{name:30}{Style.RESET_ALL} "
                  f"Status: {status_color}{status:10}{Style.RESET_ALL} "
                  f"Health: {status_color}{health}{Style.RESET_ALL}")

        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    def run(self):
        """Run the monitoring loop."""
        print(f"{Fore.GREEN}{Style.BRIGHT}Starting Docker Health Monitor...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Check interval: {self.check_interval} seconds{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Log directory: {self.log_dir.absolute()}{Style.RESET_ALL}\n")

        try:
            while True:
                self.check_containers()
                self.print_status_summary()
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Monitoring stopped by user.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
            raise

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Monitor Docker container health and send local alerts"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Check interval in seconds (default: 10)"
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="logs",
        help="Directory for log files (default: logs)"
    )

    args = parser.parse_args()

    monitor = DockerHealthMonitor(
        check_interval=args.interval,
        log_dir=args.log_dir
    )
    monitor.run()

if __name__ == "__main__":
    main()
