import requests
import pytest
import os

# Tests should be run with an empty database.

def test_open_server():
    url = 'http://localhost:8000/'
    response = requests.get(url)

    filename = "files/index.html"
    with open(filename, 'rb') as f:
        expected_data = f.read()

    # Assert that the request is successful
    assert response.status_code == 200
    # Assert that the response data is as expected
    assert response.content == expected_data

def test_user_creation_1():
    creds = {
    'username': 'testuser',
    'password': 'abcd',
    'permission': 'admin'
    }
    response = requests.post("http://localhost:8000/createuser", json=creds)

    # Assert that the request is successful
    assert response.status_code == 200
    # Assert that the response data is as expected

    assert response.text == '{"detail":"Created account"}'

def test_user_creation_2():

    creds = {
        'username': 'testuser',
        'password': 'abcd'
    }
    loginCall = requests.post("http://localhost:8000/login", json=creds)

    userCreds = {
    'username': 'testuser2',
    'password': 'abcde',
    'permission': 'user'
    }
    response = requests.post("http://localhost:8000/createuser", json=userCreds, headers={'Authorization': f'Bearer {loginCall.json()["access_token"]}'})

    # Assert that the request is successful
    assert response.status_code == 200
    # Assert that the response data is as expected

    assert response.text == '{"detail":"Created account"}'

def test_failed_login():

    creds = {
        'username': 'nullUser',
        'password': 'abcd'
    }
    response = requests.post("http://localhost:8000/login", json=creds)

    # Assert that the request is successful
    assert not response.status_code == 200

def test_upload_file():
    filename = "README.md"

    creds = {
        'username': 'testuser',
        'password': 'abcd'
    }
    loginCall = requests.post("http://localhost:8000/login", json=creds)

    response = requests.post(f'http://localhost:8000/file/?name={filename}', files={'file': open(filename, 'rb')},
     headers={'Authorization': f'Bearer {loginCall.json()["access_token"]}'})

    # Assert that the request is successful
    assert response.status_code == 200
    # Assert that the response data is as expected
    assert response.text == '"Success!"'

def test_download_file():
    filename = "README.md"
    creds = {
        'username': 'testuser',
        'password': 'abcd'
    }
    loginCall = requests.post("http://localhost:8000/login", json=creds)

    response = requests.get(f'http://localhost:8000/file/?name={filename}', headers={'Authorization': f'Bearer {loginCall.json()["access_token"]}'})

    with open('files/testuser/' + filename, 'rb') as f:
        expected_data = f.read()

    # Assert that the request is successful
    assert response.status_code == 200
    # Assert that the response data is as expected
    assert response.content == expected_data

def test_no_access_download_file():
    # Logs in with the second user and attempts to download that the user does not own.
    filename = "README.md"
    creds = {
        'username': 'testuser2',
        'password': 'abcde'
    }
    loginCall = requests.post("http://localhost:8000/login", json=creds)

    response = requests.get(f'http://localhost:8000/file/?name={filename}?owner=testuser', headers={'Authorization': f'Bearer {loginCall.json()["access_token"]}'})

    # Assert that the request is successful
    assert response.status_code == 403