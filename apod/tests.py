import json
import datetime
from django.test import TestCase, Client
from .models import Apod, CelestialBody, Collection


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_apod(**kwargs):
    """Create a minimal valid Apod for testing."""
    defaults = dict(
        date=datetime.date(2024, 1, 1),
        title="Test APOD",
        explanation="A test image of the cosmos.",
        url="https://apod.nasa.gov/apod/image/test.jpg",
        media_type="image",
    )
    defaults.update(kwargs)
    return Apod.objects.create(**defaults)


def make_body(**kwargs):
    """Create a minimal valid CelestialBody for testing."""
    defaults = dict(
        name="Orion Nebula",
        body_type="Nebula",
        right_ascension="05h 35m 17.3s",
        declination="-05° 23' 28\"",
    )
    defaults.update(kwargs)
    return CelestialBody.objects.create(**defaults)


# ---------------------------------------------------------------------------
# Smoke Tests — do the API endpoints respond at all?
# ---------------------------------------------------------------------------

class APIEndpointSmokeTests(TestCase):
    """
    Smoke tests: verify each public API endpoint returns HTTP 200.
    These catch total failures — broken imports, missing routes, DB errors.
    They don't test the content, just that the door opens.
    """

    def setUp(self):
        self.client = Client()
        self.apod = make_apod()
        self.body = make_body()
        self.collection = Collection.objects.create(
            apod=self.apod,
            celestial_body=self.body,
        )

    def test_apods_endpoint_returns_200(self):
        response = self.client.get('/api/apods/')
        self.assertEqual(response.status_code, 200)

    def test_celestial_bodies_endpoint_returns_200(self):
        response = self.client.get('/api/celestial-bodies/')
        self.assertEqual(response.status_code, 200)

    def test_collections_endpoint_returns_200(self):
        response = self.client.get('/api/collections/')
        self.assertEqual(response.status_code, 200)

    def test_apods_returns_json_list(self):
        response = self.client.get('/api/apods/')
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Test APOD')

    def test_celestial_bodies_returns_json_list(self):
        response = self.client.get('/api/celestial-bodies/')
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(data[0]['name'], 'Orion Nebula')


# ---------------------------------------------------------------------------
# Security Tests — do our fixes actually work?
# ---------------------------------------------------------------------------

class ToolAllowlistSecurityTest(TestCase):
    """
    Verify that tool_views rejects tool names not in ALLOWED_TOOLS.
    This tests the path traversal fix we shipped in the security hardening commit.
    An attacker sending tool_name='../../etc/passwd' should get an error, not a file read.
    """

    def setUp(self):
        self.client = Client()

    def test_unknown_tool_name_returns_error(self):
        """A tool name not in the allowlist should be rejected."""
        response = self.client.post(
            '/api/tools/totally_fake_tool/',
            data=json.dumps({}),
            content_type='application/json',
        )
        # Should return 404 (no URL match) or error JSON — not a 500 or file read
        self.assertNotEqual(response.status_code, 500)

    def test_path_traversal_attempt_rejected(self):
        """A path traversal string should never reach the filesystem."""
        from apod.tool_views import _run_script
        result = json.loads(_run_script('../../etc/passwd', {}))
        self.assertIn('error', result)

    def test_allowed_tool_name_passes_validation(self):
        """A valid tool name should pass the allowlist check (even if the script fails)."""
        from apod.tool_views import _run_script, ALLOWED_TOOLS
        # All five expected tools should be in the allowlist
        expected = {
            'get_celestial_bodies',
            'get_todays_apod',
            'get_visible_tonight',
            'lookup_simbad',
            'lookup_jpl_horizons',
        }
        self.assertEqual(ALLOWED_TOOLS, expected)


class ADQLSanitizationTest(TestCase):
    """
    Verify that _sanitize_adql_name correctly neutralizes injection attempts.
    This tests the ADQL injection fix in simbad.py.
    """

    def setUp(self):
        from apod.simbad import _sanitize_adql_name
        self.sanitize = _sanitize_adql_name

    def test_single_quotes_are_stripped(self):
        """Single quotes should be stripped entirely — eliminates ADQL injection surface."""
        result = self.sanitize("M 31' OR '1'='1")
        self.assertNotIn("'", result)  # No quotes survive

    def test_normal_name_passes_through(self):
        """A normal astronomical name should survive sanitization unchanged."""
        result = self.sanitize("Orion Nebula")
        self.assertEqual(result, "Orion Nebula")

    def test_ngc_name_passes_through(self):
        """NGC catalog names with numbers and spaces should pass through."""
        result = self.sanitize("NGC 1499")
        self.assertEqual(result, "NGC 1499")

    def test_empty_string_is_safe(self):
        """An empty string should not raise an error."""
        result = self.sanitize("")
        self.assertEqual(result, "")


# ---------------------------------------------------------------------------
# Unit Tests — does the astronomy math produce correct results?
# ---------------------------------------------------------------------------

class AstronomyUtilsTest(TestCase):
    """
    Unit tests for deg_to_hms and deg_to_dms in _astronomy_utils.py.
    These functions convert coordinate formats used in SIMBAD/JPL responses.
    """

    def setUp(self):
        import sys, os
        scripts_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'skill', 'scripts'
        )
        sys.path.insert(0, scripts_dir)
        from _astronomy_utils import deg_to_hms, deg_to_dms
        self.deg_to_hms = deg_to_hms
        self.deg_to_dms = deg_to_dms

    def test_deg_to_hms_zero(self):
        """0 degrees RA = 0 hours."""
        result = self.deg_to_hms(0)
        self.assertTrue(result.startswith("00h"))

    def test_deg_to_hms_180_degrees(self):
        """180 degrees = 12 hours exactly."""
        result = self.deg_to_hms(180)
        self.assertTrue(result.startswith("12h"))

    def test_deg_to_hms_360_degrees(self):
        """360 degrees = 24 hours (full circle)."""
        result = self.deg_to_hms(360)
        self.assertTrue(result.startswith("24h"))

    def test_deg_to_dms_positive(self):
        """Positive declination gets a + sign."""
        result = self.deg_to_dms(45)
        self.assertTrue(result.startswith("+"))

    def test_deg_to_dms_negative(self):
        """Negative declination gets a - sign."""
        result = self.deg_to_dms(-30)
        self.assertTrue(result.startswith("-"))

    def test_deg_to_dms_zero(self):
        """Zero declination is treated as positive."""
        result = self.deg_to_dms(0)
        self.assertTrue(result.startswith("+"))
