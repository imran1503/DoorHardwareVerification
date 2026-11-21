"""Project schedule import and saved per-door verification tests."""
import base64
import gc
import hashlib
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from contextlib import closing
from unittest.mock import patch

from pypdf import PdfWriter

from src.server import database
from src.server.api import Handler


class ResponseHarness:
    def send_json(self, data, status=200):
        self.response = (status, data)
        return self.response


class ScheduleImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = database.DB_PATH
        database.DB_PATH = Path(cls.temp_dir.name) / "schedule-test.db"
        database.initialize()

    @classmethod
    def tearDownClass(cls):
        database.DB_PATH = cls.db_path
        gc.collect()
        cls.temp_dir.cleanup()

    @staticmethod
    def blank_pdf():
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        output = BytesIO()
        writer.write(output)
        return output.getvalue()

    def test_imported_schedule_is_persisted_and_confirmed_matches_are_saved_per_door(self):
        products = [
            ("exit_device", "626QED111-MLR"),
            ("hinge", "628661HD-CE-12EA"),
        ]
        parsed = {
            "pages": [{"page_number": 1, "text": "Hardware set 1\nD101  Single door  Set 1"}],
            "doors": [{"door_number": "D101", "heading_number": "1", "description": "Single door", "raw": "D101  Single door  Set 1", "page": 1, "source_row_number": 10001}],
            "sets": [{"set_code": "1", "description": "Exterior electrified door", "start_page": 1, "end_page": 1, "notes": ""}],
            "items": [
                {"set_code": "1", "source_row_number": 10002, "quantity": 1, "sku": "626QED111-MLR", "units": "EA", "description": "626QED111-MLR exit device", "raw": "1 626QED111-MLR EA exit device", "page": 1},
                {"set_code": "1", "source_row_number": 10003, "quantity": 1, "sku": "628661HD-CE-12EA", "units": "EA", "description": "628661HD-CE-12EA electric hinge", "raw": "1 628661HD-CE-12EA EA electric hinge", "page": 1},
            ],
            "issues": [],
        }
        payload = {
            "name": "Test hardware project",
            "filename": "schedule.pdf",
            "revision_label": "A",
            "file_base64": base64.b64encode(self.blank_pdf()).decode("ascii"),
        }
        harness = ResponseHarness()
        upload_dir = Path(self.temp_dir.name) / "uploads"
        with patch("src.server.api.extract_schedule", return_value=parsed), patch("src.server.api.SCHEDULE_UPLOAD_DIR", upload_dir):
            with closing(database.connect()) as db:
                Handler.import_schedule(harness, db, payload)
                db.commit()
        status, imported = harness.response
        self.assertEqual(status, 201)
        self.assertEqual(imported["counts"], {"pages": 1, "doors": 1, "sets": 1, "items": 2, "review_issues": 0})
        self.assertTrue((upload_dir / f"{hashlib.sha256(self.blank_pdf()).hexdigest()}.pdf").is_file())

        with closing(database.connect()) as db:
            detail = ResponseHarness()
            Handler.get_project(detail, db, imported["project_id"])
            door = detail.response[1]["doors"][0]
            self.assertEqual(door["door_number"], "D101")
            items = door["assignments"][0]["items"]
            self.assertEqual(len(items), 2)
            product_ids = [items[0]["matches"][0]["product"]["id"], items[1]["matches"][0]["product"]["id"]]
            for item, product_id in zip(items, product_ids):
                saved = ResponseHarness()
                Handler.save_schedule_match(saved, db, {"scheduled_item_id": item["id"], "product_id": product_id, "review_status": "confirmed"})
                self.assertEqual(saved.response[0], 200)
            verified = ResponseHarness()
            Handler.verify_project(verified, db, imported["project_id"], {"run_name": "Review run"})
            self.assertEqual(verified.response[0], 201)
            run_id = verified.response[1]["run_id"]
            run = ResponseHarness()
            Handler.get_verification_run(run, db, run_id)
        self.assertEqual(run.response[1]["doors"][0]["door_number"], "D101")
        self.assertEqual(run.response[1]["doors"][0]["result"]["status"], "compatible")

    def test_invalid_pdf_is_rejected_without_creating_a_project(self):
        harness = ResponseHarness()
        with closing(database.connect()) as db:
            Handler.import_schedule(harness, db, {"name": "Bad", "filename": "x.pdf", "file_base64": base64.b64encode(b"not a pdf").decode("ascii")})
            count = db.execute("SELECT COUNT(*) FROM projects WHERE name='Bad'").fetchone()[0]
        self.assertEqual(harness.response[0], 400)
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
