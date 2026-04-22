import os
import anthropic
from apod.models import CelestialBody, Collection

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
    body, created = CelestialBody.objects.get_or_create(
        name=name,
        defaults={
            "body_type": body_type,
            "right_ascension": right_ascension,
            "declination": declination,
            "description": description,
        }
    )
    apod = Apod.objects.get(date=apod_date)
    Collection.objects.get_or_create(apod=apod, celestial_body=body)
    return f"Saved {name} and linked to APOD {apod_date}."

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
            system="You are an expert astronomer. Analyze this Astronomy Picture of the Day. Identify the primary celestial body featured, check if it has been collected before, and save it. When saving, provide the real right ascension and declination from your astronomy knowledge — for example '05h 35m 17s' and '-05° 23' 28\"'. For objects with variable positions like comets, provide their approximate coordinates at time of observation if known, otherwise use 'unknown'. When naming celestial bodies, always use the scientific designation without prefixes — for example use 'C/2025 R3 (PanSTARRS)' not 'Comet C/2025 R3 (PanSTARRS)'.",
            tools=TOOLS,
            messages=messages,
            cache_control={"type": "ephemeral"},
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
