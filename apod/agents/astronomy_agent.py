import os
import logging
import anthropic
from apod.models import CelestialBody, Collection
from apod.simbad import validate_against_simbad, validate_range
from apod.jpl_horizons import is_solar_system_body, validate_against_horizons

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

TOOLS = [
    {
        "name": "search_previous_apods",
        "description": "Check if a celestial body has already been collected in the database",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The name of the celestial body"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "save_celestial_body",
        "description": "Save a celestial body and link it to an APOD entry as a collection",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "body_type": {"type": "string"},
                "right_ascension": {"type": "string"},
                "declination": {"type": "string"},
                "description": {"type": "string"},
                "apod_date": {"type": "string", "description": "The APOD date in YYYY-MM-DD format"}
            },
            "required": ["name", "body_type", "right_ascension", "declination", "apod_date"]
        }
    }
]


def search_previous_apods(name):
    exists = CelestialBody.objects.filter(name__icontains=name).exists()
    if exists:
        return f"{name} has already been collected."
    return f"{name} has not been collected yet."


def save_celestial_body(name, body_type, right_ascension, declination, apod_date, description=""):
    from apod.models import Apod

    # Step 1: Validate coordinate ranges
    range_valid, range_msg = validate_range(right_ascension, declination)
    if not range_valid:
        logger.warning(f"Invalid coordinates for '{name}': {range_msg}")
        return f"VALIDATION ERROR: {range_msg}. Please provide valid coordinates."

    # Step 2: Cross-reference with SIMBAD (deep-sky objects)
    validation = validate_against_simbad(name, right_ascension, declination)
    logger.info(f"SIMBAD validation for '{name}': {validation['message']}")

    # Step 3: If SIMBAD didn't find it, try JPL Horizons (solar system objects)
    horizons_validation = None
    if not validation["simbad_found"]:
        logger.info(f"SIMBAD miss for '{name}', trying JPL Horizons...")
        horizons_validation = validate_against_horizons(
            name, right_ascension, declination, date=apod_date
        )
        logger.info(f"JPL Horizons validation for '{name}': {horizons_validation['message']}")

    # Step 4: Save (even if sources disagree, but log the discrepancy)
    defaults = {
        "body_type": body_type,
        "right_ascension": right_ascension,
        "declination": declination,
        "description": description,
    }

    # Enrich description with whichever source confirmed
    if validation["simbad_found"] and validation["simbad_data"]:
        simbad = validation["simbad_data"]
        canonical_note = f" [SIMBAD: {simbad['main_id']}, type: {simbad['object_type']}]"
        if description:
            defaults["description"] = description + canonical_note
        else:
            defaults["description"] = canonical_note
    elif horizons_validation and horizons_validation["horizons_found"] and horizons_validation["horizons_data"]:
        horizons = horizons_validation["horizons_data"]
        canonical_note = f" [JPL Horizons: {horizons['body_name']}, type: {horizons['body_type']}]"
        if description:
            defaults["description"] = description + canonical_note
        else:
            defaults["description"] = canonical_note

    body, created = CelestialBody.objects.get_or_create(
        name=name,
        defaults=defaults,
    )
    apod = Apod.objects.get(date=apod_date)
    Collection.objects.get_or_create(apod=apod, celestial_body=body)

    # Build response message
    result = f"Saved {name} and linked to APOD {apod_date}."
    if validation["simbad_found"]:
        result += f" SIMBAD: {validation['message']}"
    elif horizons_validation and horizons_validation["horizons_found"]:
        result += f" JPL Horizons: {horizons_validation['message']}"
    if not validation["validated"]:
        if horizons_validation and not horizons_validation.get("validated", True):
            result += " WARNING: Coordinate discrepancy detected by both sources."
        elif not validation["simbad_found"]:
            pass  # SIMBAD not finding it isn't a warning
        else:
            result += " WARNING: Coordinate discrepancy detected."

    return result


def execute_tool(name, tool_input):
    if name == "search_previous_apods":
        return search_previous_apods(tool_input["name"])
    elif name == "save_celestial_body":
        return save_celestial_body(**tool_input)
    return "Unknown tool"


def analyze_apod(apod):
    messages = [{"role": "user", "content": f"Title: {apod.title}\n\nExplanation: {apod.explanation}\n\nDate: {apod.date}"}]
    max_turns = 8

    for _ in range(max_turns):
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            system=[{
                "type": "text",
                "text": "You are an expert astronomer. Analyze this Astronomy Picture of the Day. Identify the primary celestial body featured, check if it has been collected before, and save it. When saving, provide the real right ascension and declination from your astronomy knowledge — for example '05h 35m 17s' and '-05° 23' 28\"'. For objects with variable positions like comets, provide their approximate coordinates at time of observation if known, otherwise use 'unknown'. When naming celestial bodies, always use the scientific designation without prefixes — for example use 'C/2025 R3 (PanSTARRS)' not 'Comet C/2025 R3 (PanSTARRS)'.",
                "cache_control": {"type": "ephemeral"},
            }],
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })

        if not tool_results:
            break

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    return response
