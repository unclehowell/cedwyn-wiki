"""Static regression guard for the Wiki-specific duplicate navigation bar."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
css = (ROOT / "wp-content/themes/h4/global.css").read_text(encoding="utf-8")
target = '.ghf-estate-bar > [role="navigation"][aria-label="The Legal Wiki"]'

# Only the Wiki-local navigation is suppressed. The shared Cedwyn shell is not.
match = re.search(re.escape(target) + r"\s*\{([^}]*)\}", css)
assert match, "the targeted Wiki-specific navigation rule is missing"
assert re.search(r"display\s*:\s*none\s*!important", match.group(1)), "the redundant nav is not hidden"
assert not re.search(r"\.ghf-estate-bar\s*\{[^}]*display\s*:\s*none", css), "the shared outer bar must remain visible"
assert "[aria-label=\"Legal Wiki & Evidence\"]" not in target, "the shared shell navigation must not be targeted"
print("PASS: only the page-level The Legal Wiki navigation is hidden; the shared shell bar is preserved")
