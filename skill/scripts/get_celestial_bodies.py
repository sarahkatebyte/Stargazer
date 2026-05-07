import json
import os
import urllib.request

BASE_URL = os.environ.get('STARGAZER_BASE_URL', 'http://localhost:8000').rstrip('/')
response = urllib.request.urlopen(f'{BASE_URL}/api/celestial-bodies/')
data = json.loads(response.read())
print(json.dumps(data))
