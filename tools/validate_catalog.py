import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
data = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
if data.get("schema_version") != 1 or not isinstance(data.get("resources"), list):
    raise SystemExit("Invalid catalog")
seen = set()
for item in data["resources"]:
    for field in ("path", "source", "revision", "license", "sha256", "compatibility"):
        if not isinstance(item.get(field), str) or not item[field].strip():
            raise SystemExit(f"Missing {field}")
    rel = Path(item["path"])
    path = (root / rel).resolve()
    if rel.is_absolute() or not path.is_relative_to(root) or not path.is_file() or path in seen:
        raise SystemExit("Invalid or duplicate resource path")
    seen.add(path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
        raise SystemExit(f"Hash mismatch: {rel}")
print(f"Validated {len(seen)} catalog entries (integrity only)")
