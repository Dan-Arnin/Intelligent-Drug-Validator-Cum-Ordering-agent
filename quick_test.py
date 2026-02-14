import requests
import json

# Simple test to trigger logging
response = requests.post(
    "http://localhost:8000/api/v1/medical-chat",
    json={
        "message": "Hello test",
        "conversation_history": [],
        "medical_information": None,
        "prescription_data": None
    }
)

print("Status:", response.status_code)
print("\nResponse:")
print(json.dumps(response.json(), indent=2))
