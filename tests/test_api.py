"""API logic tests using an isolated SQLite database and no network sockets."""
import json
import gc
from pathlib import Path
import tempfile
import unittest
from collections import Counter
from contextlib import closing
from unittest.mock import patch

from src.server import database
from src.server.api import Handler
from src.server.compatibility import assembly_subset_checks


class ResponseHarness:
    def send_json(self, data, status=200):
        self.response = (status, data)
        return self.response


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = database.DB_PATH
        database.DB_PATH = Path(cls.temp_dir.name) / "test.db"
        database.initialize()

    @classmethod
    def tearDownClass(cls):
        database.DB_PATH = cls.db_path
        gc.collect()
        cls.temp_dir.cleanup()

    def test_database_initializes_seeded_catalog(self):
        with closing(database.connect()) as db:
            products = db.execute("SELECT count(*) FROM products WHERE active=1").fetchone()[0]
            kit = db.execute("SELECT id FROM products WHERE model='CX-WC17SLVR'").fetchone()
        self.assertGreater(products, 0)
        self.assertIsNotNone(kit)

    def test_documented_kit_assertion_is_compatible(self):
        with closing(database.connect()) as db:
            kit = db.execute("SELECT id FROM products WHERE model='CX-WC17SLVR'").fetchone()["id"]
            controller = db.execute("SELECT id FROM products WHERE model='CX-33'").fetchone()["id"]
        harness = ResponseHarness()

        Handler.check_assembly(harness, {"product_ids": [kit, controller]})

        status, result = harness.response
        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "likely_compatible")
        self.assertTrue(result["findings"])
        self.assertEqual(result["subset_checks"], [])
        self.assertTrue(any(finding.get("status") == "compatible" for finding in result["findings"]))
        self.assertTrue(any(finding.get("finding_type") == "power_path" and finding.get("status") == "conditional" for finding in result["findings"]))

    def test_six_product_assembly_lists_all_57_subsets_without_pair_evaluation(self):
        models = ("CX-WC17SLVR", "CX-33", "CM-8536VR", "CM-221", "CX-PS13", "CX-TRX-4024")
        with closing(database.connect()) as db:
            ids = [
                db.execute("SELECT id FROM products WHERE model=? ORDER BY id LIMIT 1", (model,)).fetchone()["id"]
                for model in models
            ]
        harness = ResponseHarness()

        with patch("src.server.api.pair_evaluation") as pair_evaluation, patch("src.server.api.pair_estimate") as pair_estimate:
            Handler.check_assembly(harness, {"product_ids": ids})

        status, result = harness.response
        self.assertEqual(status, 200)
        self.assertEqual(len(result["subset_checks"]), 57)
        self.assertEqual(
            Counter(check["subset_size"] for check in result["subset_checks"]),
            {2: 15, 3: 20, 4: 15, 5: 6, 6: 1},
        )
        self.assertEqual(result["estimate"]["checks_in_average"], 1)
        self.assertEqual(result["estimate"]["applicable_pairs"], 0)
        pair_evaluation.assert_not_called()
        pair_estimate.assert_not_called()
        full_tuple = next(check for check in result["subset_checks"] if check["subset_size"] == 6)
        self.assertEqual(full_tuple["status"], "compatible")
        self.assertTrue(full_tuple["has_exact_assertion"])
        self.assertEqual(full_tuple["source_url"], "/evidence/camden/WC17SLVR_Restroom_Control_Manual_R2.pdf#page=8")
        self.assertTrue(any(not check["has_exact_assertion"] for check in result["subset_checks"]))

    def test_subset_count_uses_power_set_minus_empty_and_singletons(self):
        with closing(database.connect()) as db:
            products = [database.product_dict(row) for row in db.execute("SELECT * FROM products WHERE active=1 ORDER BY id LIMIT 8")]
            for size in range(3, 9):
                checks = assembly_subset_checks(db, products[:size])
                self.assertEqual(len(checks), 2**size - size - 1)

    def test_unknown_legacy_combination_stays_unverified(self):
        harness = ResponseHarness()

        Handler.check(harness, {"door_material": "unknown"})

        status, result = harness.response
        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "unverified")

    def test_serializers_preserve_json_specifications(self):
        with closing(database.connect()) as db:
            product = database.product_dict(db.execute("SELECT * FROM products WHERE model='CX-33'").fetchone())
        self.assertEqual(product["specifications"]["record_scope"], "exact_model")
        self.assertEqual(json.loads(json.dumps(product))["model"], "CX-33")


if __name__ == "__main__":
    unittest.main()
