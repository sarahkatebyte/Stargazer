"""
Shared astronomy utility functions used across Stargazer tool scripts.
Import with: sys.path.insert(0, os.path.dirname(__file__)) then from _astronomy_utils import ...
"""

import re


def deg_to_hms(deg: float) -> str:
    """Convert degrees to hours/minutes/seconds string (used for RA)."""
    hours = deg / 15.0
    h = int(hours)
    m = int((hours - h) * 60)
    s = ((hours - h) * 60 - m) * 60
    return f"{h:02d}h {m:02d}m {s:04.1f}s"


def deg_to_dms(deg: float) -> str:
    """Convert degrees to degrees/arcminutes/arcseconds string (used for Dec)."""
    sign = "+" if deg >= 0 else "-"
    d = int(abs(deg))
    m = int((abs(deg) - d) * 60)
    s = ((abs(deg) - d) * 60 - m) * 60
    return f"{sign}{d:02d}\u00b0 {m:02d}' {s:04.1f}\""


def sanitize_adql_name(name: str) -> str:
    """
    Sanitize a celestial body name for safe interpolation into ADQL queries.
    Escapes single quotes (ADQL standard) and strips non-astronomical characters.
    """
    name = name.replace("'", "''")
    name = re.sub(r'[^\w\s\-+.*/()\[\]#,]', '', name)
    return name.strip()
