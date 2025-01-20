import Fastify from "fastify";
import { Postgres } from "./postgres";
import { www } from "./www";
import { Discord } from "./discord";

const fastify = Fastify({ logger: true });
const pg = new Postgres({
  host: process.env.POSTGRES_HOST || "localhost",
  port: +(process.env.POSTGRES_PORT || 5432),
  user: process.env.POSTGRES_USER || "oblivion",
  password: process.env.POSTGRESS_PASS || "oblivion",
  database: process.env.POSTGRES_DB || "oblivionis",
});

const dc = new Discord(process.env.DISCORD_TOKEN!);
const w = new www(pg, dc);

// Routes
fastify.get("/", async (request, reply) => {
  reply.type("text/html").send(await w.frontPage());
});

fastify.get("/users", async (request, reply) => {
  reply.type("text/html").send(await w.usersPage());
});

fastify.get("/games", async (request, reply) => {
  reply.type("text/html").send(await w.gamesPage());
});

fastify.get("/user/:id", async (request, reply) => {
  const { id } = request.params as { id: string };
  reply.type("text/html").send(await w.userPage(id));
});

fastify.get("/user/:id/json", async (request, reply) => {
  const { id } = request.params as { id: string };
  reply.type("application/json").send(await w.getUserData(id));
});

fastify.listen(
  { port: +(process.env.PORT || 8000), host: "0.0.0.0" },
  (err, address) => {
    if (err) {
      console.error("Error starting server:", err);
      process.exit(1);
    }
    console.log(`Server is running at ${address}`);
  }
);
