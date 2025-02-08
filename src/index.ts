import Fastify from "fastify";
import { Postgres } from "./postgres";
import { www } from "./www";
import { Discord } from "./discord";
import { Totals } from "./totals";

const PROD = process.env.NODE_ENV === "production";

export class STATICS {
  static discord = new Discord(process.env.DISCORD_TOKEN!);
  static fastify = Fastify({ logger: true });
  static pg = new Postgres({
    host: process.env.POSTGRES_HOST || "localhost",
    port: +(process.env.POSTGRES_PORT || 5432),
    user: process.env.POSTGRES_USER || "oblivion",
    password: process.env.POSTGRESS_PASS || "oblivion",
    database: process.env.POSTGRES_DB || "oblivionis",
  });
  static web = new www();
  static totals = new Totals();
}

const cacheAge = +(process.env.CACHE_AGE || 60 * 1000);
const cache = new Map<string, any>();

function getCache(url: string): string | null {
  if (!PROD) {
    // annoying when developing
    return null;
  }
  if (!cache.has(url)) {
    console.warn(url, "is not cached :(");
    return null;
  }
  console.warn(url, "is cached! :D");
  return cache.get(url);
}

function cacheAndReturn(url: string, data: any): any {
  cache.set(url, data);
  setTimeout(() => {
    cache.delete(url);
    console.warn(url, "cache expired");
  }, cacheAge);
  return data;
}

// Routes
STATICS.fastify.get("/", async (request, reply) => {
  const cache = getCache(request.url);
  if (cache) {
    return reply.type("text/html").send(cache);
  }

  reply
    .type("text/html")
    .send(cacheAndReturn(request.url, await STATICS.web.frontPage()));
});

/* Games */

STATICS.fastify.get("/game/:id", async (request, reply) => {
  const cache = getCache(request.url);
  if (cache) {
    return reply.type("text/html").send(cache);
  }
  const { id } = request.params as { id: string };

  reply
    .type("text/html")
    .send(cacheAndReturn(request.url, await STATICS.web.gamePage(+id)));
});

STATICS.fastify.get("/game/:id/chartData", async (request, reply) => {
  const cache = getCache(request.url);
  if (cache) {
    return reply.send(cache);
  }

  const { id } = request.params as { id: number };
  const game = await STATICS.pg.fetchGame(id);
  if (!game) {
    reply.code(400).send("Could not get game");
    return;
  }

  reply.send(cacheAndReturn(request.url, await game.chartData()));
});

STATICS.fastify.get("/games", async (request, reply) => {
  const cache = getCache(request.url);
  if (cache) {
    return reply.type("text/html").send(cache);
  }

  reply
    .type("text/html")
    .send(cacheAndReturn(request.url, await STATICS.web.gamesPage()));
});

/* Users */

STATICS.fastify.get("/users", async (request, reply) => {
  const cache = getCache(request.url);
  if (cache) {
    return reply.type("text/html").send(cache);
  }

  reply
    .type("text/html")
    .send(cacheAndReturn(request.url, await STATICS.web.usersPage()));
});

STATICS.fastify.get("/user/:id", async (request, reply) => {
  const cache = getCache(request.url);
  if (cache) {
    return reply.type("text/html").send(cache);
  }
  const { id } = request.params as { id: string };
  const html = await STATICS.web.userPage(id);

  reply.type("text/html").send(cacheAndReturn(request.url, html));
});

STATICS.fastify.get("/user/:id/chartData", async (request, reply) => {
  const cache = getCache(request.url);
  if (cache) {
    return reply.send(cache);
  }
  const { id } = request.params as { id: string };
  const user = await STATICS.pg.fetchUser(id);
  if (!user) {
    reply.code(400).send("Could not get user");
    return;
  }
  reply.send(cacheAndReturn(request.url, await user.chartData()));
});

/* Totals */

STATICS.fastify.get("/totals/chartData", async (request, reply) => {
  const cache = getCache(request.url);
  if (cache) {
    return reply.send(cache);
  }
  reply.send(cacheAndReturn(request.url, await STATICS.totals.chartData()));
});

// end of routes

STATICS.fastify.listen(
  { port: +(process.env.PORT || 8000), host: "0.0.0.0" },
  (err, address) => {
    if (err) {
      console.error("Error starting server:", err);
      process.exit(1);
    }
    console.log(`Server is running at ${address}`);
  }
);
