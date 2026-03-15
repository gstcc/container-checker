from flask import Flask, jsonify
import os
import time
import sys

app = Flask(__name__)

START_TIME = time.time()
CRASH_AFTER = int(os.environ.get("CRASH_AFTER", 45))


@app.route("/")
def index():
    uptime = int(time.time() - START_TIME)

    if uptime >= CRASH_AFTER:
        print(f"Uptime {uptime}s exceeded {CRASH_AFTER}s - CRASHING!", flush=True)
        sys.exit(1)

    return jsonify(
        {
            "status": "running",
            "app": "crashing-app",
            "uptime_seconds": uptime,
            "message": f"Will crash after {CRASH_AFTER}s",
        }
    )


@app.route("/health")
def health():
    """Health check endpoint."""
    uptime = int(time.time() - START_TIME)

    if uptime >= CRASH_AFTER:
        print(f"Uptime {uptime}s exceeded {CRASH_AFTER}s - CRASHING!", flush=True)
        sys.exit(1)

    return (
        jsonify(
            {
                "status": "healthy",
                "uptime": uptime,
                "message": f"Healthy (will crash in {CRASH_AFTER - uptime}s)",
            }
        ),
        200,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port)
