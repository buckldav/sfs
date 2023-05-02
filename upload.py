#
#  UPLOAD TO API EXAMPLE
#

import requests
import os

filename = "README.md"
files = {'file': open(f'{filename}', 'rb')}

creds = {
    'username': 'testuser',
    'password': 'abcd'
}

loginCall = requests.post("http://localhost:8000/login", json=creds)

try:
    if loginCall.json()['access_token'] != None:
        uploadCall = requests.post(
            f"http://localhost:8000/file/?name={filename}", files=files, headers={'Authorization': f'Bearer {loginCall.json()["access_token"]}'})
        print(uploadCall.text)

except:
    print("Failed to authenticate.")
