from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data" / "source"
NEGATIVE_DIR = ROOT / "data" / "negative"
DB_PATH = ROOT / "runtime" / "rxguard.db"
REFRESH_LOG = ROOT / "runtime" / "refresh_log.csv"

COLORS = {
    "navy": "#14324A",
    "blue": "#2878B5",
    "teal": "#22A699",
    "green": "#4C9F70",
    "amber": "#E4A11B",
    "red": "#C94C4C",
    "slate": "#64748B",
    "light": "#E8EEF4",
}

CHART_COLORS = ["#2878B5", "#22A699", "#E4A11B", "#7E57C2", "#C94C4C", "#64748B"]
