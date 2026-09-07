"""Validate the current Compose image and AgentOS data persistence in isolation."""
import json
import socket
import subprocess
import tempfile
import time
import os
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]


def run(args, **kwargs):
    try:
        return subprocess.run(args, check=True, text=True, capture_output=True, **kwargs)
    except subprocess.CalledProcessError as exc:
        detail = ((exc.stdout or "") + "\n" + (exc.stderr or "")).strip()
        raise RuntimeError(detail or f"command failed: {' '.join(args)}") from exc


with tempfile.TemporaryDirectory() as temporary:
    temporary = Path(temporary)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]
    project = "agentosvalidation" + str(int(time.time()))
    environment = {**os.environ, "AGENTOS_PORT": str(port)}
    compose = ["docker", "compose", "-p", project, "-f", str(ROOT / "compose.yaml")]
    try:
        run([*compose, "up", "--build", "-d"], env=environment)
        for _ in range(90):
            try:
                if json.load(urlopen(f"http://127.0.0.1:{port}/healthz", timeout=2)).get("ok"):
                    break
            except OSError:
                pass
            time.sleep(1)
        else:
            raise RuntimeError("Compose health check did not become ready.")
        # This uses AgentOS's own persistent store, never the owner's local data.
        run([*compose, "exec", "-T", "agentos", "python", "-c", "import sqlite3,time; c=sqlite3.connect('/data/private/quickstart.db'); c.execute(\"INSERT INTO notes VALUES (?,?,?)\",('compose-persistence-proof','compose-persistence-proof',time.time())); c.commit()"], env=environment)
        run([*compose, "down"], env=environment)
        run([*compose, "up", "-d"], env=environment)
        check = run([*compose, "exec", "-T", "agentos", "python", "-c", "import sqlite3; c=sqlite3.connect('/data/private/quickstart.db'); assert c.execute(\"SELECT 1 FROM notes WHERE content='compose-persistence-proof'\").fetchone()"], env=environment)
        print(json.dumps({"compose_health": True, "recreated_container": True, "persistent_agentos_store": check.returncode == 0}))
    finally:
        subprocess.run([*compose, "down", "--volumes", "--remove-orphans"], text=True, capture_output=True, env=environment)
