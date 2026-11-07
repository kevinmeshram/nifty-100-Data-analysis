import importlib
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

PACKAGES = {
    "pandas": "pandas", "numpy": "numpy", "openpyxl": "openpyxl",
    "xlsxwriter": "xlsxwriter", "sqlalchemy": "sqlalchemy",
    "python-dotenv": "dotenv", "pytest": "pytest", "pytest-cov": "pytest_cov",
    "scipy": "scipy", "matplotlib": "matplotlib", "seaborn": "seaborn",
    "plotly": "plotly", "streamlit": "streamlit", "fastapi": "fastapi",
    "uvicorn": "uvicorn", "pydantic": "pydantic", "requests": "requests",
    "jinja2": "jinja2", "reportlab": "reportlab", "jupyter": "jupyter_core",
}

missing = []
for package, module in PACKAGES.items():
    try:
        importlib.import_module(module)
    except ImportError:
        missing.append(package)

print("Libraries checked:", len(PACKAGES))
print("Libraries missing:", missing)
print("DB_PATH from .env:", os.getenv("DB_PATH"))
print("Project root exists:", ROOT.is_dir())

assert not missing, f"Install these libraries: {missing}"
assert os.getenv("DB_PATH"), "DB_PATH is missing in .env"
print("Environment OK")