"""
Test script for the Medicine Verification Service API.
"""
import requests
import os
from pathlib import Path


def test_health_check():
    """Test the health check endpoint."""
    print("Testing health check endpoint...")
    response = requests.get("http://localhost:8000/api/v1/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_upload_prescription(file_path: str):
    """
    Test the prescription upload endpoint.
    
    Args:
        file_path: Path to the prescription file to upload
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return
    
    print(f"Testing prescription upload with file: {file_path}")
    
    url = "http://localhost:8000/api/v1/upload-prescription"
    
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        response = requests.post(url, files=files)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['success']}")
        
        if data['success']:
            print("\n=== Extracted Data ===")
            
            # Doctor Info
            if data['data'].get('doctor_info'):
                print("\nDoctor Information:")
                for key, value in data['data']['doctor_info'].items():
                    if value:
                        print(f"  {key}: {value}")
            
            # Patient Info
            if data['data'].get('patient_info'):
                print("\nPatient Information:")
                for key, value in data['data']['patient_info'].items():
                    if value:
                        print(f"  {key}: {value}")
            
            # Medicines
            if data['data'].get('medicines'):
                print(f"\nMedicines ({len(data['data']['medicines'])} found):")
                for i, medicine in enumerate(data['data']['medicines'], 1):
                    print(f"\n  Medicine {i}:")
                    for key, value in medicine.items():
                        if value:
                            print(f"    {key}: {value}")
        else:
            print(f"Error: {data.get('error')}")
            if data.get('raw_response'):
                print(f"Raw Response: {data['raw_response'][:500]}...")
    else:
        print(f"Error Response: {response.text}")
    
    print()


def main():
    """Main test function."""
    print("=" * 60)
    print("Medicine Verification Service - Test Script")
    print("=" * 60)
    print()
    
    # Test health check
    try:
        test_health_check()
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to the service.")
        print("Make sure the service is running on http://localhost:8000")
        print("Run: python main.py")
        return
    
    # Test prescription upload
    print("To test prescription upload, provide a file path:")
    print("Example: python test_api.py path/to/prescription.jpg")
    print()
    
    # Check if file path is provided as command line argument
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        test_upload_prescription(file_path)
    else:
        print("No file provided. Skipping upload test.")
        print("Usage: python test_api.py <path_to_prescription_file>")


if __name__ == "__main__":
    main()
