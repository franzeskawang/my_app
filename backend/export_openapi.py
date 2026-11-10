"""Export FastAPI's OpenAPI document for shared client contract generation."""
import json
from pathlib import Path

from app.main import app

output_path = Path(__file__).resolve().parent / "openapi.json"
output_path.write_text(
    json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(f"Exported OpenAPI schema to {output_path}")
