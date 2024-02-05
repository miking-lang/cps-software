# Server For Remote Control of the Spider

Build docker and run it with docker-compose.

For debian, install:

 * `docker.io`
 * `docker-compose`

From this directory, start the server by

```sh
sudo docker-compose up -d
```

View stdout prints with: (-f to continue listen for more output)

```sh
sudo docker-compose logs -f
```

Stop the server by

```sh
sudo docker-compose down
```

