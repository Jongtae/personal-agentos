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
    # This development acceptance must not inherit a developer's provider
    # allowlist or credential-like Compose configuration. The empty policy
    # keeps engine egress default-deny while exercising local lifecycle only.
    environment = {**os.environ, "AGENTOS_PORT": str(port), "COMPOSE_PROJECT_NAME": project,
                   "AGENTOS_PROVIDER_EGRESS_ALLOWLIST": ""}
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
        run([*compose, "exec", "-T", "agentos", "python", "-c", "import sqlite3,json; c=sqlite3.connect('/data/private/quickstart.db'); c.execute(\"INSERT INTO config VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value\",('telegram',json.dumps({'enabled':True,'generation':'compose-proof','user_id':42}))); c.commit()"], env=environment)
        run([*compose, "down"], env=environment)
        run([*compose, "up", "-d"], env=environment)
        continuity = run([*compose, "exec", "-T", "agentos", "python", "-c", "import sqlite3,json; c=sqlite3.connect('/data/private/quickstart.db'); assert c.execute(\"SELECT 1 FROM notes WHERE content='compose-persistence-proof'\").fetchone(); assert json.loads(c.execute(\"SELECT value FROM config WHERE key='telegram'\").fetchone()[0])['user_id']==42"], env=environment)
        # A portable archive is intentionally secret-free: restore proves state
        # recovery, while the Telegram token/pairing must be re-established.
        temporary.chmod(0o777)
        archive = temporary / "owner-state.tar.gz"
        run([str(ROOT / "scripts" / "compose-backup.sh"), str(archive)], env=environment)
        run([*compose, "down", "--volumes"], env=environment)
        run([str(ROOT / "scripts" / "compose-restore.sh"), str(archive)], env=environment)
        run([*compose, "up", "-d"], env=environment)
        restored = run([*compose, "exec", "-T", "agentos", "python", "-c", "import sqlite3; c=sqlite3.connect('/data/private/quickstart.db'); assert c.execute(\"SELECT 1 FROM notes WHERE content='compose-persistence-proof'\").fetchone(); assert not c.execute(\"SELECT 1 FROM config WHERE key='telegram'\").fetchone()"], env=environment)
        print(json.dumps({"compose_health": True, "recreated_container": True, "telegram_pairing_continues_on_recreate": continuity.returncode == 0, "portable_restore": restored.returncode == 0, "portable_restore_requires_telegram_reconnection": True}))
    finally:
        subprocess.run([*compose, "down", "--volumes", "--remove-orphans"], text=True, capture_output=True, env=environment)
