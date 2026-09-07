"""Local, contract-validated compatibility A2A test-peer adapter."""
import time
import uuid

TERMINAL = {"completed", "failed", "canceled", "timed-out"}
STATES = {"requested", "working", "input-required", *TERMINAL}


class A2AError(ValueError): pass


class A2ADelegation:
    def __init__(self, store, peer, now=time.time): self.store,self.peer,self.now=store,peer,now
    def _all(self): return self.store.config("a2a_delegations", {})
    def _put(self, rows): self.store.put("a2a_delegations", rows)
    def discover(self):
        card=self.peer.card()
        if not isinstance(card,dict) or card.get("protocol")!="a2a/1" or card.get("skill")!="bounded-research" or not card.get("artifact_schema"):
            raise A2AError("Compatibility peer card is unsupported.")
        return {"peer":"compatibility-a2a-peer","skill":card["skill"]}
    def delegate(self, owner_request):
        if not isinstance(owner_request,dict) or owner_request.get("explicit") is not True or not isinstance(owner_request.get("prompt"),str) or not owner_request["prompt"].strip():
            raise A2AError("Explicit owner delegation is required.")
        card=self.discover(); ident=str(uuid.uuid4()); correlation=str(uuid.uuid4())
        remote=self.peer.create({"delegation_id":ident,"correlation_id":correlation,"prompt":owner_request["prompt"].strip(),"skill":card["skill"]})
        if not isinstance(remote,dict) or remote.get("correlation_id")!=correlation: raise A2AError("Peer correlation mismatch.")
        rows=self._all(); rows[ident]={"id":ident,"state":"requested","correlation_id":correlation,"peer":card["peer"],"skill":card["skill"],"created_at":self.now(),"artifacts":[]}; self._put(rows)
        return self.status(ident)
    def status(self, ident):
        rows=self._all(); row=rows.get(ident)
        if not row: raise A2AError("Delegation not found.")
        if row["state"] in TERMINAL:return dict(row)
        event=self.peer.status(ident,row["correlation_id"])
        if not isinstance(event,dict) or event.get("correlation_id")!=row["correlation_id"] or event.get("state") not in STATES: raise A2AError("Peer status is invalid.")
        state=event["state"]
        if state in TERMINAL and state=="completed":
            artifact=event.get("artifact")
            if not isinstance(artifact,dict) or not isinstance(artifact.get("text"),str) or len(artifact["text"])>12000: state="failed"; row["error"]="invalid-artifact"
            else: row["artifacts"]=[{"id":artifact.get("id","artifact"),"text":artifact["text"]}]
        row["state"]=state; row["updated_at"]=self.now(); rows[ident]=row; self._put(rows); return dict(row)
    def cancel(self, ident):
        rows=self._all(); row=rows.get(ident)
        if not row: raise A2AError("Delegation not found.")
        if row["state"] not in TERMINAL:self.peer.cancel(ident,row["correlation_id"]);row["state"]="canceled";row["updated_at"]=self.now();rows[ident]=row;self._put(rows)
        return dict(row)
    def artifact(self, ident, artifact_id):
        row=self.status(ident)
        if row["state"]!="completed":raise A2AError("Delegation has no completed artifact.")
        return next((dict(x) for x in row["artifacts"] if x["id"]==artifact_id),None)
