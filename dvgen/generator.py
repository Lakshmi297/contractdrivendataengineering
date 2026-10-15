"""Validate JSON contracts and generate BigQuery Data Vault 2.0 DDL."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class ContractError(ValueError):
    """Raised when a contract does not satisfy the generator's contract rules."""


_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
_PROJECT_ID = re.compile(r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")
_BIGQUERY_TYPES = {
    "BIGNUMERIC",
    "BOOL",
    "BYTES",
    "DATE",
    "DATETIME",
    "FLOAT64",
    "GEOGRAPHY",
    "INT64",
    "JSON",
    "NUMERIC",
    "STRING",
    "TIME",
    "TIMESTAMP",
}


def validate_contract(contract: Any) -> dict[str, Any]:
    """Validate the complete contract and return it as a typed dictionary."""
    errors: list[str] = []
    if not isinstance(contract, dict):
        raise ContractError("Contract root must be a JSON object.")

    if contract.get("contract_version") != "1.0":
        errors.append("contract_version must be '1.0'.")
    _validate_target(contract.get("target"), errors)
    _require_identifier(contract.get("source_system"), "source_system", errors)

    entities = contract.get("entities")
    if not isinstance(entities, list) or not entities:
        errors.append("entities must be a non-empty array.")
        entities = []

    entity_names: set[str] = set()
    for index, entity in enumerate(entities):
        path = f"entities[{index}]"
        if not isinstance(entity, dict):
            errors.append(f"{path} must be an object.")
            continue
        name = entity.get("name")
        _require_identifier(name, f"{path}.name", errors)
        if isinstance(name, str):
            if name in entity_names:
                errors.append(f"{path}.name duplicates entity '{name}'.")
            entity_names.add(name)
        keys = entity.get("business_keys")
        _validate_fields(keys, f"{path}.business_keys", errors, require=True)
        if isinstance(name, str) and isinstance(keys, list):
            _reject_reserved_fields(
                keys,
                {f"{name}_hk", "load_datetime", "record_source"},
                f"{path}.business_keys",
                errors,
            )
        satellites = entity.get("satellites", [])
        _validate_satellites(satellites, f"{path}.satellites", errors)
        if isinstance(name, str) and isinstance(satellites, list):
            for sat_index, satellite in enumerate(satellites):
                if isinstance(satellite, dict) and isinstance(
                    satellite.get("attributes"), list
                ):
                    _reject_reserved_fields(
                        satellite["attributes"],
                        {
                            f"{name}_hk",
                            "load_datetime",
                            "record_source",
                            "hashdiff",
                        },
                        f"{path}.satellites[{sat_index}].attributes",
                        errors,
                    )

    relationships = contract.get("relationships")
    if not isinstance(relationships, list) or not relationships:
        errors.append("relationships must be a non-empty array.")
        relationships = []
    relationship_names: set[str] = set()
    for index, relationship in enumerate(relationships):
        path = f"relationships[{index}]"
        if not isinstance(relationship, dict):
            errors.append(f"{path} must be an object.")
            continue
        name = relationship.get("name")
        _require_identifier(name, f"{path}.name", errors)
        if isinstance(name, str):
            if name in relationship_names:
                errors.append(f"{path}.name duplicates relationship '{name}'.")
            relationship_names.add(name)
        members = relationship.get("members")
        if not isinstance(members, list) or len(members) < 2:
            errors.append(f"{path}.members must contain at least two entity names.")
        else:
            if any(not isinstance(member, str) for member in members):
                errors.append(f"{path}.members must contain only entity names.")
            elif len(set(members)) != len(members):
                errors.append(f"{path}.members must not contain duplicates.")
            else:
                if name in members:
                    errors.append(
                        f"{path}.name must differ from every member entity name."
                    )
                for member in members:
                    if member not in entity_names:
                        errors.append(
                            f"{path}.members references unknown entity '{member}'."
                        )
        satellite = relationship.get("satellite")
        if satellite is not None:
            _validate_satellites([satellite], f"{path}.satellite", errors)
            if (
                isinstance(name, str)
                and isinstance(satellite, dict)
                and isinstance(satellite.get("attributes"), list)
            ):
                _reject_reserved_fields(
                    satellite["attributes"],
                    {
                        f"{name}_hk",
                        "load_datetime",
                        "record_source",
                        "hashdiff",
                    },
                    f"{path}.satellite.attributes",
                    errors,
                )

    has_entity_satellites = any(
        isinstance(entity, dict) and entity.get("satellites")
        for entity in entities
    )
    has_link_satellites = any(
        isinstance(relationship, dict) and relationship.get("satellite")
        for relationship in relationships
    )
    if not has_entity_satellites and not has_link_satellites:
        errors.append("The Data Vault model must declare at least one Satellite.")

    if errors:
        raise ContractError("Contract validation failed:\n- " + "\n- ".join(errors))
    return contract


def render_ddl(contract: Any) -> str:
    """Validate a contract and render its BigQuery DDL without writing files."""
    valid = validate_contract(contract)
    target = valid["target"]
    project = target["project_id"]
    dataset = target["dataset"]
    statements: list[str] = [
        "-- Generated from a validated contract. Do not edit by hand.",
        f"-- Data Vault 2.0 DDL target: {project}.{dataset}",
    ]

    for entity in valid["entities"]:
        name = entity["name"]
        hub_columns = [
            (f"{name}_hk", "STRING", True),
            *[
                (field["name"], field["type"], True)
                for field in entity["business_keys"]
            ],
            ("load_datetime", "TIMESTAMP", True),
            ("record_source", "STRING", True),
        ]
        statements.append(_create_table(project, dataset, f"hub_{name}", hub_columns))
        for satellite in entity.get("satellites", []):
            sat_name = f"sat_{name}_{satellite['name']}"
            sat_columns = _satellite_columns(
                f"{name}_hk", satellite["attributes"]
            )
            statements.append(_create_table(project, dataset, sat_name, sat_columns))

    for relationship in valid.get("relationships", []):
        name = relationship["name"]
        link_columns = [
            (f"{name}_hk", "STRING", True),
            *[(f"{member}_hk", "STRING", True) for member in relationship["members"]],
            ("load_datetime", "TIMESTAMP", True),
            ("record_source", "STRING", True),
        ]
        statements.append(
            _create_table(project, dataset, f"link_{name}", link_columns)
        )
        satellite = relationship.get("satellite")
        if satellite:
            sat_name = f"sat_{name}_{satellite['name']}"
            sat_columns = _satellite_columns(f"{name}_hk", satellite["attributes"])
            statements.append(_create_table(project, dataset, sat_name, sat_columns))

    return "\n\n".join(statements).rstrip() + "\n"


def generate_ddl(contract_path: Path, output_dir: Path) -> int:
    """Validate and generate one DDL file; return the generated table count."""
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractError(
            f"Invalid JSON in {contract_path} at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc
    ddl = render_ddl(contract)
    table_count = ddl.count("CREATE TABLE IF NOT EXISTS")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "data_vault_ddl.sql").write_text(ddl, encoding="utf-8", newline="\n")
    return table_count


def _validate_target(target: Any, errors: list[str]) -> None:
    if not isinstance(target, dict):
        errors.append("target must be an object.")
        return
    if target.get("provider") != "gcp":
        errors.append("target.provider must be 'gcp'.")
    if target.get("service") != "bigquery":
        errors.append("target.service must be 'bigquery'.")
    project_id = target.get("project_id")
    if not isinstance(project_id, str) or not _PROJECT_ID.fullmatch(project_id):
        errors.append("target.project_id must be a valid GCP project ID.")
    _require_identifier(target.get("dataset"), "target.dataset", errors)
    location = target.get("location")
    if not isinstance(location, str) or not location.strip():
        errors.append("target.location must be a non-empty string.")


def _validate_fields(
    fields: Any, path: str, errors: list[str], *, require: bool
) -> None:
    if not isinstance(fields, list) or (require and not fields):
        expected = "a non-empty array" if require else "an array"
        errors.append(f"{path} must be {expected}.")
        return
    names: set[str] = set()
    for index, field in enumerate(fields):
        field_path = f"{path}[{index}]"
        if not isinstance(field, dict):
            errors.append(f"{field_path} must be an object.")
            continue
        name = field.get("name")
        _require_identifier(name, f"{field_path}.name", errors)
        if isinstance(name, str):
            if name in names:
                errors.append(f"{field_path}.name duplicates field '{name}'.")
            names.add(name)
        sql_type = field.get("type")
        if not isinstance(sql_type, str) or sql_type.upper() not in _BIGQUERY_TYPES:
            errors.append(
                f"{field_path}.type must be a supported BigQuery Standard SQL type."
            )
        elif sql_type != sql_type.upper():
            field["type"] = sql_type.upper()


def _validate_satellites(
    satellites: Any,
    path: str,
    errors: list[str],
) -> None:
    if not isinstance(satellites, list):
        errors.append(f"{path} must be an array.")
        return
    names: set[str] = set()
    for index, satellite in enumerate(satellites):
        sat_path = f"{path}[{index}]"
        if not isinstance(satellite, dict):
            errors.append(f"{sat_path} must be an object.")
            continue
        name = satellite.get("name")
        _require_identifier(name, f"{sat_path}.name", errors)
        if isinstance(name, str):
            if name in names:
                errors.append(f"{sat_path}.name duplicates satellite '{name}'.")
            names.add(name)
        attributes = satellite.get("attributes")
        _validate_fields(
            attributes,
            f"{sat_path}.attributes",
            errors,
            require=True,
        )


def _require_identifier(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        errors.append(
            f"{path} must start with a letter or underscore and contain only "
            "letters, digits, or underscores (max 128 characters)."
        )


def _reject_reserved_fields(
    fields: list[dict[str, Any]],
    reserved: set[str],
    path: str,
    errors: list[str],
) -> None:
    for index, field in enumerate(fields):
        if isinstance(field, dict) and field.get("name") in reserved:
            errors.append(
                f"{path}[{index}].name '{field['name']}' conflicts with a "
                "Data Vault system column."
            )


def _satellite_columns(
    parent_hash_key: str, attributes: list[dict[str, str]]
) -> list[tuple[str, str, bool]]:
    return [
        (parent_hash_key, "STRING", True),
        ("load_datetime", "TIMESTAMP", True),
        ("record_source", "STRING", True),
        ("hashdiff", "STRING", True),
        *[(field["name"], field["type"], False) for field in attributes],
    ]


def _create_table(
    project: str,
    dataset: str,
    table: str,
    columns: list[tuple[str, str, bool]],
) -> str:
    column_lines = [
        f"  `{name}` {sql_type}{' NOT NULL' if required else ''}"
        for name, sql_type, required in columns
    ]
    return (
        f"CREATE TABLE IF NOT EXISTS `{project}.{dataset}.{table}` (\n"
        + ",\n".join(column_lines)
        + "\n);"
    )
