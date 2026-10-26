"""Per-role default-output transaction, independent of GUI and COM bindings."""

import json
import os
from pathlib import Path
import uuid
import psutil


class RoutingJournal:
    def __init__(self, path):
        self.path = Path(path)

    def write(self, state):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(self.path.name + ".tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(state, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, self.path)

    def clear(self):
        self.path.unlink(missing_ok=True)


class OutputRouting:
    """Call only on the backend's thread; notifications only enqueue plain data."""

    def __init__(self, backend, journal):
        self.backend = backend
        self.journal = journal
        self.state = None

    def prepare(self, target, communications=False):
        if self.state is not None:
            raise RuntimeError("Output routing transaction already active")
        if not self.backend.available(target):
            raise RuntimeError("Virtual output endpoint unavailable")
        if self.journal.path.exists():
            raise RuntimeError("An unfinished routing journal requires recovery before automatic switching")
        self.backend.changes()  # Changes before the snapshot belong to earlier activity.
        roles = (0, 1, 2) if communications else (0, 1)
        self.state = dict(schema_version=1, session_id=str(uuid.uuid4()), pid=os.getpid(),
                          process_created=psutil.Process().create_time(),
                          target=target, phase="prepared", roles={
                              str(role): dict(before=self.backend.default(role), owned=False,
                                              relinquished=False) for role in roles})
        try:
            self.journal.write(self.state)
        except BaseException:
            self.state = None
            raise

    def load_recovery(self):
        if self.state is not None:
            raise RuntimeError("Cannot recover over an active routing transaction")
        state = json.loads(self.journal.path.read_text(encoding="utf-8"))
        if (state.get("schema_version") != 1 or not isinstance(state.get("target"), str)
                or not state["target"] or not isinstance(state.get("roles"), dict)
                or not state["roles"] or not isinstance(state.get("pid"), int)
                or state["pid"] <= 0 or not isinstance(state.get("process_created"), (int, float))):
            raise RuntimeError("Invalid routing recovery journal")
        for role, entry in state["roles"].items():
            if (role not in ("0", "1", "2") or not isinstance(entry, dict)
                    or not isinstance(entry.get("owned"), bool)
                    or not isinstance(entry.get("relinquished"), bool)
                    or not (entry.get("before") is None or isinstance(entry["before"], str))):
                raise RuntimeError("Invalid routing role in recovery journal")
        try:
            owner = psutil.Process(state["pid"])
            same_process = owner.create_time() == state["process_created"]
            own_failed_cleanup = state["pid"] == os.getpid() and state.get("phase") == "restore_failed"
            if same_process and not own_failed_cleanup:
                raise RuntimeError("Routing journal belongs to a running process")
        except psutil.NoSuchProcess:
            pass
        # Recovery is explicit and still restores only matching, owned roles.
        self.backend.changes()
        self.state = state

    def observe(self):
        if self.state is None:
            return
        changed = False
        for role, endpoint in self.backend.changes():
            entry = self.state["roles"].get(str(role))
            if entry is None:
                continue
            expected = self.state["target"] if entry["owned"] else entry["before"]
            if endpoint != expected and not entry["relinquished"]:
                entry.update(owned=False, relinquished=True)
                changed = True
        if changed:
            self.journal.write(self.state)

    def activate(self):
        if self.state is None:
            raise RuntimeError("Routing must be prepared before activation")
        self.observe()
        target = self.state["target"]
        try:
            for key, entry in self.state["roles"].items():
                self.observe()
                role = int(key)
                if entry["relinquished"] or entry["before"] == target:
                    continue
                if self.backend.default(role) != entry["before"]:
                    entry["relinquished"] = True
                    self.journal.write(self.state)
                    continue
                # Write intent before mutation; a partial API failure can still change Windows.
                entry["owned"] = True
                self.journal.write(self.state)
                self.backend.set_default(target, role)
            self.state["phase"] = "active"
            self.journal.write(self.state)
        except BaseException:
            self.restore()
            raise

    def restore(self):
        if self.state is None:
            return []
        self.observe()
        failures = []
        target = self.state["target"]
        for key, entry in self.state["roles"].items():
            role = int(key)
            if not entry["owned"]:
                continue
            try:
                if self.backend.default(role) != target:
                    entry.update(owned=False, relinquished=True)
                elif self.backend.available(entry["before"]):
                    self.backend.set_default(entry["before"], role)
                    entry["owned"] = False
                else:
                    failures.append(f"Previous output unavailable for role {role}")
            except Exception as exc:
                failures.append(f"Could not restore role {role}: {exc}")
        if failures:
            self.state["phase"] = "restore_failed"
            self.journal.write(self.state)
        else:
            self.journal.clear()
            self.state = None
        return failures
