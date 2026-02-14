"""
Test script for the new medicine safety and medical chat endpoints.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_medicine_safety():
    """Test the medicine safety check endpoint."""
    print("\n" + "="*60)
    print("Testing Medicine Safety Check Endpoint")
    print("="*60)
    
    # Test data
    payload = {
        "medicines": [
            "Paracetamol",
            "Alprazolam",
            "Codeine",
            "Aspirin",
            "Phenylpropanolamine"
        ]
    }
    
    print(f"\nChecking safety for medicines: {payload['medicines']}")
    
    response = requests.post(f"{BASE_URL}/check-medicine-safety", json=payload)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"\nResponse:")
    print(json.dumps(response.json(), indent=2))
    
    return response.json()


def test_medical_chat():
    """Test the medical chat endpoint."""
    print("\n" + "="*60)
    print("Testing Medical Chat Endpoint")
    print("="*60)
    
    # Test conversation flow
    conversations = [
        {
            "message": "Hello",
            "conversation_history": [],
            "medical_information": None,
            "prescription_data": None
        },
        {
            "message": "I have a fever and headache for the past 3 days",
            "conversation_history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hello, I'm here to help collect information about your medical prescription details. To begin, can you tell me what disease or illness you are currently suffering from and what are the symptoms?"}
            ],
            "medical_information": None,
            "prescription_data": None
        },
        {
            "message": "The doctor prescribed Paracetamol 500mg and Ibuprofen",
            "conversation_history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hello, I'm here to help..."},
                {"role": "user", "content": "I have a fever and headache for the past 3 days"},
                {"role": "assistant", "content": "Thank you for sharing that."}
            ],
            "medical_information": {
                "reported_disease": "fever and headache",
                "medications_provided_by_user": None,
                "medication_confirmation": None
            },
            "prescription_data": None
        }
    ]
    
    for i, conv in enumerate(conversations, 1):
        print(f"\n--- Conversation Turn {i} ---")
        print(f"User: {conv['message']}")
        
        response = requests.post(f"{BASE_URL}/medical-chat", json=conv)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nAssistant: {result.get('response', 'No response')}")
            print(f"Conversation Complete: {result.get('conversation_complete', False)}")
            
            if result.get('updated_medical_information'):
                print(f"\nCollected Information:")
                print(json.dumps(result['updated_medical_information'], indent=2))
        else:
            print(f"Error: {response.text}")
        
        print()


def test_health():
    """Test the health check endpoint."""
    print("\n" + "="*60)
    print("Testing Health Check Endpoint")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.json()}")


if __name__ == "__main__":
    try:
        # Test health first
        test_health()
        
        # Test medicine safety
        test_medicine_safety()
        
        # Test medical chat
        test_medical_chat()
        
        print("\n" + "="*60)
        print("All tests completed!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the server.")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
