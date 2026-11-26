# Документация / Documentation

The authoritative design baseline is in [Aeris-Core/docs](https://github.com/geliopat/Aeris-Core/tree/main/docs). Read the project [AGENTS.md](../AGENTS.md) before changes. Specification files are requirements, not implementation evidence.

- [SPECIFICATION.md](https://github.com/geliopat/Aeris-Core/blob/main/docs/SPECIFICATION.md)
- [ARCHITECTURE.md](https://github.com/geliopat/Aeris-Core/blob/main/docs/ARCHITECTURE.md)
- [CONFIGURATION.md](https://github.com/geliopat/Aeris-Core/blob/main/docs/CONFIGURATION.md)
- [PROVIDER-HEADERS.md](https://github.com/geliopat/Aeris-Core/blob/main/docs/PROVIDER-HEADERS.md)
- [UI-SPECIFICATION.md](https://github.com/geliopat/Aeris-Core/blob/main/docs/UI-SPECIFICATION.md)
- [ROADMAP.md](https://github.com/geliopat/Aeris-Core/blob/main/docs/ROADMAP.md)
- [TESTING.md](https://github.com/geliopat/Aeris-Core/blob/main/docs/TESTING.md)
- [COMPATIBILITY.md](https://github.com/geliopat/Aeris-Core/blob/main/docs/COMPATIBILITY.md)

## Catalog integrity checks

Run `python tools/validate_catalog.py` and `python -m unittest discover -s tools -p 'test_*.py'` with Python 3.12. The validator expects files under the checkout at relative paths with forward slashes. It rejects links, ambiguous paths, duplicate JSON keys and incorrect SHA-256 digests. Tests use synthetic resources. Source, revision, license and compatibility fields are checked for presence. Signing, license review and runtime compatibility have separate acceptance criteria in Aeris-Core.
