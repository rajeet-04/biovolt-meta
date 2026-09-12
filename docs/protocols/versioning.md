# Protocol Versioning

Every protocol document contains `schema_version` as an integer.
Phase 0 defines version `1`.

Compatible additions may extend a v1 schema only when old valid v1 payloads remain valid.
Breaking changes create a new schema file such as `device-telemetry.v2.schema.json`.
Existing v1 files are never silently repurposed with incompatible meanings.
