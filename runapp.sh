# Refresh docker container in case port is already in use.
docker stop $(docker ps -a -q --filter="ancestor=halverneus/static-file-server:latest")
# Start new docker container. If port is in use, change 8080:8080 to {port}:8080.
docker run -d -v $PWD/files/:/web -p 8080:8080 halverneus/static-file-server:latest
if [ ! -f .env ]
then
    # Sets up a .env file with a default values.
    touch .env
    echo $'SECRETKEY=5d5e6a74-b8db-476a-ae3f-cc18812bab80
FILESERVERURL=http://127.0.0.1:8080
MONGOURL=mongodb://127.0.0.1:27017' > .env
fi
# Starts the API to communicate with docker container.
uvicorn api:app --reload