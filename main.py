import os
import subprocess
from pathlib import Path

from flask import Flask, jsonify, request, send_file

app = Flask(__name__)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.get("/")
def index():
    return {
        "service": "test-agent",
        "status": "running"
    }


@app.get("/ls")
def list_files():
    files = []

    for root, _, filenames in os.walk("."):
        for f in filenames:
            files.append(os.path.join(root, f))

    return jsonify(sorted(files))


@app.post("/up/<filename>")
def upload(filename):
    filepath = UPLOAD_DIR / filename

    with open(filepath, "wb") as f:
        f.write(request.data)

    return {
        "saved": str(filepath),
        "size": filepath.stat().st_size
    }


@app.get("/dl/<filename>")
def download(filename):
    filepath = UPLOAD_DIR / filename

    if not filepath.exists():
        return {"error": "file not found"}, 404

    return send_file(filepath)


@app.post("/run")
def run():

    body = request.get_json(force=True)

    command = body.get("command")

    timeout = int(body.get("timeout", 30))

    if not command:
        return {"error": "command missing"}, 400

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except subprocess.TimeoutExpired:
        return {
            "error": "command timed out"
        }, 408

    except Exception as e:
        return {
            "error": str(e)
        }, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
