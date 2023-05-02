## Static FileServer API

An api for a static fileserver based on `https://github.com/halverneus/static-file-server`.

Running the fileserver:
`docker run -d -v $PWD/files/:/web -p 8080:8080 halverneus/static-file-server:latest`

Running the api:
`uvicorn api:app --reload`

Example for downloading a file from the api is located at `./download.py`.
 * Downloaded files will appear in `./downloads/`
Example for uploading a file from the api is located at `./upload.py`.

Fileserver files located in `./files/`.

Quickly deploy:
`sudo bash runapp.sh`
 * Requirements may need to be installed again with sudo privileges.

 API Information: 
 Found at http://localhost:8000/
