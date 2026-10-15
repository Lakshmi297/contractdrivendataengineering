"""Tests for contract validation and generated BigQuery Data Vault DDL."""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from dvgen.generator import ContractError, generate_ddl, render_ddl


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "pilot-contract.json"


class GeneratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_generates_hubs_links_entity_satellites_and_link_satellite(self) -> None:
        ddl = render_ddl(self.contract)

        self.assertIn("`demo-data-dev.dv_stage0.hub_customer`", ddl)
        self.assertIn("`demo-data-dev.dv_stage0.hub_order`", ddl)
        self.assertIn("`demo-data-dev.dv_stage0.link_customer_order`", ddl)
        self.assertIn("`demo-data-dev.dv_stage0.sat_customer_profile`", ddl)
        self.assertIn("`demo-data-dev.dv_stage0.sat_order_details`", ddl)
        self.assertIn("`demo-data-dev.dv_stage0.sat_customer_order_context`", ddl)
        self.assertIn("`customer_id` STRING NOT NULL", ddl)
        self.assertIn("`relationship_status` STRING", ddl)

    def test_rejects_invalid_contract_before_creating_output(self) -> None:
        invalid = copy.deepcopy(self.contract)
        invalid["relationships"][0]["members"] = ["customer", "missing_entity"]
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "invalid.json"
            output = Path(temp) / "generated"
            source.write_text(json.dumps(invalid), encoding="utf-8")

            with self.assertRaisesRegex(ContractError, "unknown entity"):
                generate_ddl(source, output)

            self.assertFalse(output.exists())

    def test_rejects_unsafe_sql_type(self) -> None:
        invalid = copy.deepcopy(self.contract)
        invalid["entities"][0]["business_keys"][0]["type"] = "STRING); DROP TABLE x"
        with self.assertRaisesRegex(ContractError, "supported BigQuery"):
            render_ddl(invalid)

    def test_rejects_missing_business_key(self) -> None:
        invalid = copy.deepcopy(self.contract)
        invalid["entities"][0]["business_keys"] = []
        with self.assertRaisesRegex(ContractError, "business_keys"):
            render_ddl(invalid)

    def test_rejects_attribute_that_collides_with_system_column(self) -> None:
        invalid = copy.deepcopy(self.contract)
        invalid["entities"][0]["satellites"][0]["attributes"][0]["name"] = (
            "load_datetime"
        )
        with self.assertRaisesRegex(ContractError, "system column"):
            render_ddl(invalid)

    def test_rejects_model_without_relationships(self) -> None:
        invalid = copy.deepcopy(self.contract)
        invalid["relationships"] = []
        with self.assertRaisesRegex(ContractError, "non-empty array"):
            render_ddl(invalid)

    def test_cli_writes_expected_ddl(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "generated"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "dvgen",
                    str(EXAMPLE),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            generated = output / "data_vault_ddl.sql"
            self.assertTrue(generated.is_file())
            self.assertIn("sat_customer_order_context", generated.read_text())


if __name__ == "__main__":
    unittest.main()
