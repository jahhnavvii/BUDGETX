import requests
import json
import time

def test_registration():
    url = "http://localhost:8000/api/register"
    username = f"testuser_{int(time.time())}"
    password = "testpassword123"
    payload = {
        "username": username,
        "password": password
    }
    
    print(f"Attempting to register user: {username}")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Successfully created account!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Registration failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_registration()
