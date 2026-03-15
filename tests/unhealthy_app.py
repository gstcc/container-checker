from flask import Flask, jsonify
import os
import time

app = Flask(__name__)

START_TIME = time.time()
UNHEALTHY_AFTER = int(os.environ.get("UNHEALTHY_AFTER", 30))


@app.route("/")
def index():
    uptime = int(time.time() - START_TIME)
    is_healthy = uptime < UNHEALTHY_AFTER

    return jsonify(
        {
            "status": "running",
            "app": "unhealthy-app",
            "uptime_seconds": uptime,
            "healthy": is_healthy,
            "message": f"Will become unhealthy after {UNHEALTHY_AFTER}s",
        }
    )


@app.route("/health")
def health():
    """Health check endpoint - becomes unhealthy after UNHEALTHY_AFTER seconds."""
    uptime = int(time.time() - START_TIME)

    if uptime < UNHEALTHY_AFTER:
        return (
            jsonify(
                {
                    "status": "healthy",
                    "uptime": uptime,
                    "message": f"Healthy (will fail in {UNHEALTHY_AFTER - uptime}s)",
                }
            ),
            200,
        )
    else:
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "uptime": uptime,
                    "message": "Health check failed!",
                }
            ),
            503,
        )  # Service Unavailable


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
