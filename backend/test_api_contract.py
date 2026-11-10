"""Check the committed client contract matches FastAPI's current OpenAPI schema."""
import json
import unittest
from pathlib import Path

from app.main import app


class ApiContractTests(unittest.TestCase):
    def test_openapi_document_is_current(self):
        schema_path = Path(__file__).with_name("openapi.json")
        committed_schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(committed_schema, app.openapi())

    def test_public_success_responses_have_explicit_schemas(self):
        schema = app.openapi()
        paths = schema["paths"]
        self.assertIn("$ref", paths["/api/expenses"]["post"]["responses"]["200"]["content"]["application/json"]["schema"])
        self.assertIn("$ref", paths["/api/conversations/{conversation_id}/context"]["get"]["responses"]["200"]["content"]["application/json"]["schema"])
        self.assertEqual(paths["/api/conversations/{conversation_id}/turns"]["post"]["responses"]["204"]["description"], "Successful Response")


if __name__ == "__main__":
    unittest.main()
