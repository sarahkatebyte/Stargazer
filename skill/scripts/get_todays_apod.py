import urllib.request
import json
from datetime import date

today = date.today().isoformat()
response = urllib.request.urlopen(f'http://localhost:8000/api/apods/{today}/')
data = json.loads(response.read())
print(json.dumps(data))
