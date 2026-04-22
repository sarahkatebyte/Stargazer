import urllib.request
import json

response = urllib.request.urlopen('http://localhost:8000/api/celestial-bodies/')
data = json.loads(response.read())
print(json.dumps(data))
