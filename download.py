#
#  DOWNLOAD FROM API EXAMPLE
#

import requests
import os

filenameDir = "runapp.sh"

creds = {
    'username': 'testuser',
    'password': 'abcd'
}

loginCall = requests.post("http://localhost:8000/login", json=creds)

try:
    downloadCall = requests.get(f"http://localhost:8000/file/?name={filenameDir}", headers={
                                'Authorization': f'Bearer {loginCall.json()["access_token"]}'})
    print(downloadCall.text)

    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    filename = filenameDir.split('/')

    f = open(f"downloads/{filename[len(filename) - 1]}", "wb")
    if type(downloadCall.content) == bytes:
        f.write(downloadCall.content)
    f.close()
except:
    print("Failed to authenticate.")
