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

export interface htmlCache {
  html: string;
  timestamp: number;
}

const cacheAge = 60 * 1000;
const htmlCache = new Map<string, htmlCache>();

function getCache(url: string): string | null {
  if (!PROD) {
    // annoying when developing
    return null;
  }
  if (!htmlCache.has(url)) {
    return null;
  }
  const cached = htmlCache.get(url)!;
  const age = Date.now() - cached.timestamp;
  if (age > cacheAge) {
    return null;
  }
  console.warn("using cache for", url);
  return cached.html;
}

// Routes
STATICS.fastify.get("/", async (request, reply) => {
  const cache = getCache(request.url);
  if (cache) {
    return reply.type("text/html").send(cache);
  }
  const html = await STATICS.web.frontPage();
  htmlCache.set(request.url, { html: html, timestamp: Date.now() });
  reply.type("text/html").send(html);
});

/* Games */

STATICS.fastify.get("/game/:id", async (request, reply) => {
  const cache = getCache(request.url);
  if (cache) {
    return reply.type("text/html").send(cache);
  }
  const { id } = request.params as { id: string };
  const html = await STATICS.web.gamePage(+id);
  htmlCache.set(request.url, { html: html, timestamp: Date.now() });
  reply.type("text/html").send(html);
});

STATICS.fastify.get("/games", async (request, reply) => {
  const cache = getCache(request.url);
  if (cache) {
    return reply.type("text/html").send(cache);
  }
  const html = await STATICS.web.gamesPage();
  htmlCache.set(request.url, { html: html, timestamp: Date.now() });
  reply.type("text/html").send(html);
});

/* Users */

STATICS.fastify.get("/users", async (request, reply) => {
  const cache = getCache(request.url);
  if (cache) {
    return reply.type("text/html").send(cache);
  }
  const html = await STATICS.web.usersPage();
  htmlCache.set(request.url, { html: html, timestamp: Date.now() });
  reply.type("text/html").send(html);
});

STATICS.fastify.get("/user/:id", async (request, reply) => {
  const cache = getCache(request.url);
  if (cache) {
    return reply.type("text/html").send(cache);
  }
  const { id } = request.params as { id: string };
  const html = await STATICS.web.userPage(id);
  htmlCache.set(request.url, { html: html, timestamp: Date.now() });
  reply.type("text/html").send(html);
});

STATICS.fastify.get("/user/:id/chartData", async (request, reply) => {
  const { id } = request.params as { id: string };
  const user = await STATICS.pg.fetchUser(id);
  if (!user) {
    reply.code(400).send("Could not get user");
    return;
  }
  reply.send(await user.chartData());
});

STATICS.fastify.get("/game/:id/chartData", async (request, reply) => {
  const { id } = request.params as { id: number };
  const game = await STATICS.pg.fetchGame(id);
  if (!game) {
    reply.code(400).send("Could not get game");
    return;
  }
  reply.send(await game.chartData());
});

/* Totals */

STATICS.fastify.get("/totals/chartData", async (request, reply) => {
  reply.send(await STATICS.totals.chartData());
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
