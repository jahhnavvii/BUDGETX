import requests
import json

def test_analyze():
    url = "http://localhost:8000/api/finance/analyze"
    payload = {
        "income": 50000,
        "expense": 30000,
        "savings_rate": 0.4
    }
    
    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Success!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Failed: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_analyze()
