"""API logic tests using an isolated SQLite database and no network sockets."""
import json
from pathlib import Path
import tempfile
import unittest

from src.server import database
from src.server.api import Handler


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
        cls.temp_dir.cleanup()

    def test_database_initializes_seeded_catalog(self):
        with database.connect() as db:
            products = db.execute("SELECT count(*) FROM products WHERE active=1").fetchone()[0]
            kit = db.execute("SELECT id FROM products WHERE model='CX-WC17SLVR'").fetchone()
        self.assertGreater(products, 0)
        self.assertIsNotNone(kit)

    def test_documented_kit_assertion_is_compatible(self):
        with database.connect() as db:
            kit = db.execute("SELECT id FROM products WHERE model='CX-WC17SLVR'").fetchone()["id"]
            controller = db.execute("SELECT id FROM products WHERE model='CX-33'").fetchone()["id"]
        harness = ResponseHarness()

        Handler.check_assembly(harness, {"product_ids": [kit, controller]})

        status, result = harness.response
        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "compatible")
        self.assertTrue(result["findings"])

    def test_unknown_legacy_combination_stays_unverified(self):
        harness = ResponseHarness()

        Handler.check(harness, {"door_material": "unknown"})

        status, result = harness.response
        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "unverified")

    def test_serializers_preserve_json_specifications(self):
        with database.connect() as db:
            product = database.product_dict(db.execute("SELECT * FROM products WHERE model='CX-33'").fetchone())
        self.assertEqual(product["specifications"]["record_scope"], "exact_model")
        self.assertEqual(json.loads(json.dumps(product))["model"], "CX-33")


if __name__ == "__main__":
    unittest.main()
