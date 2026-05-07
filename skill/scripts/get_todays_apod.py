import json
import os
import urllib.request
from datetime import date

BASE_URL = os.environ.get('STARGAZER_BASE_URL', 'http://localhost:8000').rstrip('/')
today = date.today().isoformat()
response = urllib.request.urlopen(f'{BASE_URL}/api/apods/{today}/')
data = json.loads(response.read())
print(json.dumps(data))
