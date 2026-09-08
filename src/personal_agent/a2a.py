"""Local, contract-validated compatibility A2A test-peer adapter."""
import time
import uuid

TERMINAL = {"completed", "failed", "canceled", "timed-out"}
STATES = {"requested", "working", "input-required", *TERMINAL}
MAX_ARTIFACT = 12_000


class A2AError(ValueError):
    pass


class A2ADelegation:
    def __init__(self, store, peer, now=time.time, timeout_seconds=60):
        self.store, self.peer, self.now, self.timeout_seconds = store, peer, now, timeout_seconds
    def _all(self): return self.store.config("a2a_delegations", {})
    def _put(self, rows): self.store.put("a2a_delegations", rows)
    def discover(self):
        card = self.peer.card()
        if not isinstance(card, dict) or card.get("protocol") != "a2a/1" or card.get("skill") != "bounded-research" or card.get("input_schema") not in (None, "text") or card.get("artifact_schema") != "text":
            raise A2AError("Compatibility peer card is unsupported.")
        return {"peer": "compatibility-a2a-peer", "skill": card["skill"]}
    def delegate(self, request):
        if not isinstance(request, dict) or request.get("explicit") is not True or not isinstance(request.get("owner"), str) or not request["owner"] or not isinstance(request.get("prompt"), str) or not request["prompt"].strip() or len(request["prompt"]) > 12000:
            raise A2AError("Explicit owner delegation is required.")
        context = request.get("context")
        if context is not None and (not isinstance(context, dict) or set(context) != {"text"} or not isinstance(context["text"], str) or not context["text"] or len(context["text"]) > 4000):
            raise A2AError("Delegation context is invalid.")
        card = self.discover(); ident, correlation = str(uuid.uuid4()), str(uuid.uuid4())
        outbound = {"delegation_id": ident, "correlation_id": correlation, "prompt": request["prompt"].strip(), "skill": card["skill"]}
        if context is not None: outbound["context"] = context
        remote = self.peer.create(outbound)
        if not isinstance(remote, dict) or remote.get("correlation_id") != correlation: raise A2AError("Peer correlation mismatch.")
        rows = self._all(); rows[ident] = {"id": ident, "owner": request["owner"], "state": "requested", "correlation_id": correlation, "peer": card["peer"], "skill": card["skill"], "created_at": self.now(), "updated_at": self.now(), "artifacts": [], "progress": []}; self._put(rows)
        return self.status(ident, request["owner"])
    def status(self, ident, owner):
        rows = self._all(); row = rows.get(ident)
        if not row or row.get("owner") != owner: raise A2AError("Delegation not found.")
        if row["state"] in TERMINAL: return dict(row)
        if self.now() - row["created_at"] > self.timeout_seconds:
            events = [{"correlation_id": row["correlation_id"], "state": "timed-out"}]
        else:
            stream = getattr(self.peer, "events", None)
            events = stream(ident, row["correlation_id"]) if callable(stream) else [self.peer.status(ident, row["correlation_id"])]
        try: events = iter(events)
        except TypeError as exc: raise A2AError("Peer status is invalid.") from exc
        for event in events:
            if not isinstance(event, dict) or event.get("correlation_id") != row["correlation_id"] or event.get("state") not in STATES: raise A2AError("Peer status is invalid.")
            if isinstance(event.get("progress"), str): row["progress"] = [*row["progress"], event["progress"][:240]][-20:]
            state = event["state"]
            if state == "completed":
                artifact = event.get("artifact")
                if not isinstance(artifact, dict) or set(artifact) - {"id", "text"} or not isinstance(artifact.get("id"), str) or not artifact["id"] or not isinstance(artifact.get("text"), str) or len(artifact["text"]) > MAX_ARTIFACT: state, row["error"] = "failed", "invalid-artifact"
                else: row["artifacts"] = [{"id": artifact["id"], "text": artifact["text"]}]
            if state == "canceled" and row["state"] == "requested": row["error"] = "peer-canceled"
            row["state"], row["updated_at"] = state, self.now()
            if state in TERMINAL: break
        rows[ident] = row; self._put(rows); return dict(row)
    def cancel(self, ident, owner):
        rows = self._all(); row = rows.get(ident)
        if not row or row.get("owner") != owner: raise A2AError("Delegation not found.")
        if row["state"] not in TERMINAL: self.peer.cancel(ident, row["correlation_id"]); row["state"] = "canceled"; row["updated_at"] = self.now(); rows[ident] = row; self._put(rows)
        return dict(row)
    def artifact(self, ident, artifact_id, owner):
        row = self.status(ident, owner)
        if row["state"] != "completed": raise A2AError("Delegation has no completed artifact.")
        return next((dict(x) for x in row["artifacts"] if x["id"] == artifact_id), None)
