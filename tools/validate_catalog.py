"""Check the integrity and metadata shape of resources in a static checkout."""

import hashlib
import json
from pathlib import Path, PureWindowsPath
import re


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate catalog key")
        result[key] = value
    return result


def reject_constant(_value):
    raise ValueError("Invalid JSON constant in catalog")


def resource_path(root, value):
    path = root
    for part in value.split("/"):
        if (
            part in ("", ".", "..")
            or part.endswith((" ", "."))
            or re.search(r'[<>:"\\|?*\x00-\x1f\x7f\ud800-\udfff]', part)
            or PureWindowsPath(part).is_reserved()
        ):
            raise ValueError("Invalid resource path")
        path /= part
        if path.is_symlink() or path.is_junction():
            raise ValueError("Resource path contains a link")
    if not path.is_file():
        raise ValueError("Resource file does not exist")
    return path


def validate(root):
    with resource_path(root, "catalog.json").open(encoding="utf-8") as catalog:
        try:
            data = json.load(catalog, object_pairs_hook=unique_object, parse_constant=reject_constant)
        except (json.JSONDecodeError, UnicodeDecodeError, RecursionError) as error:
            raise ValueError("Invalid catalog JSON") from error
    if not isinstance(data, dict):
        raise ValueError("Invalid catalog object")
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ValueError("Invalid catalog schema version")
    if not isinstance(data.get("resources"), list):
        raise ValueError("Invalid resource list")

    seen = set()
    for index, item in enumerate(data["resources"], start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Entry {index} must be an object")
        for field in ("path", "source", "revision", "license", "sha256", "compatibility"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"Missing {field} in entry {index}")
        if re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is None:
            raise ValueError(f"Invalid SHA-256 in entry {index}")

        path = resource_path(root, item["path"])
        identity = item["path"].casefold()
        if identity in seen:
            raise ValueError(f"Duplicate resource path in entry {index}")
        seen.add(identity)
        with path.open("rb") as resource:
            if hashlib.file_digest(resource, "sha256").hexdigest() != item["sha256"]:
                raise ValueError(f"Hash mismatch in entry {index}")
    return len(seen)


if __name__ == "__main__":
    try:
        count = validate(Path(__file__).resolve().parent.parent)
    except OSError:
        raise SystemExit("Unable to read catalog or resource file") from None
    except ValueError as error:
        raise SystemExit(str(error)) from None
    print(f"Validated {count} catalog entries (integrity only)")
