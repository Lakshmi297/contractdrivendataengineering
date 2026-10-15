# Contract-Driven Data Vault Generator

This repository contains the Stage 0 starter implementation for generating
Google BigQuery Standard SQL DDL from a validated JSON contract. It generates
Data Vault 2.0 Hubs, Links, entity Satellites, and Link Satellites when a Link
has descriptive attributes.

The generator is deterministic and uses only the Python standard library.
It validates the full contract before creating the output directory or writing
DDL. It does not connect to GCP, create BigQuery resources, load data, or
calculate hash keys/hashdiff values. Those runtime/load conventions require
separate implementation and approval.

## Requirements

- Python 3.10 or later
- No third-party packages

## Generate DDL

From this repository root:

```powershell
python -m dvgen examples\pilot-contract.json --output generated
```

The command writes `generated\data_vault_ddl.sql`. It refuses to produce output
when contract validation fails and prints actionable validation errors.
An illustrative output generated from the sample contract is checked in at
[`examples/generated/data_vault_ddl.sql`](examples/generated/data_vault_ddl.sql);
it is not a selected or approved business pilot model.

Run tests:

```powershell
python -m unittest discover -s tests -v
```

## Contract shape

See [`examples/pilot-contract.json`](examples/pilot-contract.json). The
contract declares:

- A GCP project, BigQuery dataset, and location.
- Entities with one or more business keys.
- Entity Satellites with descriptive attributes.
- Relationships (Links) connecting at least two declared entities.
- Optional relationship attributes, which cause generation of a Link Satellite.

Identifiers are validated before interpolation into SQL. SQL types are selected
from a fixed BigQuery Standard SQL allowlist. Extend the allowlist only through
reviewed code changes.

## Generated Data Vault structures

- `hub_<entity>`: hash-key column, business-key columns, load timestamp, and
  record source.
- `link_<relationship>`: hash-key column, member Hub hash keys, load timestamp,
  and record source.
- `sat_<entity>_<satellite>`: parent Hub hash key, load timestamp, record
  source, hashdiff, and declared attributes.
- `sat_<relationship>_<satellite>`: parent Link hash key, load timestamp,
  record source, hashdiff, and declared relationship attributes.

Hash-key and hashdiff generation, canonicalization/null-handling rules,
multi-active/effectivity Satellites, schema evolution, ingestion, CI wiring,
BigQuery access, and production use are intentionally not implemented here.
Do not treat the example contract or generated SQL as an approved pilot model.

## Repository status

This is a local Git repository. No remote has been configured. To push it,
configure the approved Git remote and authenticate through the organization's
standard Git credential process.
