import requests

response = requests.get("http://127.0.0.1:8000/api/reports/")
print("Status Code:", response.status_code)
print("Response JSON:")
print(response.json())