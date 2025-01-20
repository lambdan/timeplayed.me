# timeplayed.me

Tracks your playtime using Discord. You just have to join the server.

Essentially a frontend for https://github.com/Hamuko/oblivionis/tree/master

![Screenshot](https://djsimg.org/59fae101549b8526587f980f36d0d534.png)

# Docker Compose

```
version: "3.7"

volumes:
  oblivionis-postgres:

services:
  oblivionis:
    image: ghcr.io/hamuko/oblivionis:latest
    container_name: oblivionis
    environment:
      DB_HOST: postgres
      DB_NAME: oblivionis
      DB_USER: oblivion
      DB_PASSWORD: oblivion
      TOKEN: - # Discord token
    restart: always
    depends_on:
      - postgres

  postgres:
    image: postgres:17.2
    restart: always
    volumes:
      - oblivionis-postgres:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: oblivion
      POSTGRES_PASSWORD: oblivion
      POSTGRES_DB: oblivionis
    ports:
      - 5432:5432

  web:
    image: playtime-tracker:latest
    ports:
      - 8000:8000
    environment:
      PORT: 8000
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_USER: oblivion
      POSTGRES_PASS: oblivion
      POSTGRES_DB: oblivionis
      DISCORD_TOKEN: -
```
