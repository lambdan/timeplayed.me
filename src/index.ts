import Fastify from "fastify";
import { Postgres } from "./postgres";
import { www } from "./www";
import { Discord } from "./discord";

const PROD = process.env.NODE_ENV === "production";

const discord = new Discord(process.env.DISCORD_TOKEN!);
const fastify = Fastify({ logger: true });
const pg = new Postgres({
  host: process.env.POSTGRES_HOST || "localhost",
  port: +(process.env.POSTGRES_PORT || 5432),
  user: process.env.POSTGRES_USER || "oblivion",
  password: process.env.POSTGRESS_PASS || "oblivion",
  database: process.env.POSTGRES_DB || "oblivionis",
});
const web = new www(pg, discord);

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
fastify.get("/", async (request, reply) => {
  const cache = getCache(request.url);
  if (cache) {
    return reply.type("text/html").send(cache);
  }
  const html = await web.frontPage();
  htmlCache.set(request.url, { html: html, timestamp: Date.now() });
  reply.type("text/html").send(html);
});

fastify.get("/users", async (request, reply) => {
  const cache = getCache(request.url);
  if (cache) {
    return reply.type("text/html").send(cache);
  }
  const html = await web.usersPage();
  htmlCache.set(request.url, { html: html, timestamp: Date.now() });
  reply.type("text/html").send(html);
});

fastify.get("/games", async (request, reply) => {
  const cache = getCache(request.url);
  if (cache) {
    return reply.type("text/html").send(cache);
  }
  const html = await web.gamesPage();
  htmlCache.set(request.url, { html: html, timestamp: Date.now() });
  reply.type("text/html").send(html);
});

fastify.get("/user/:id", async (request, reply) => {
  const cache = getCache(request.url);
  if (cache) {
    return reply.type("text/html").send(cache);
  }
  const { id } = request.params as { id: string };
  const html = await web.userPage(id);
  htmlCache.set(request.url, { html: html, timestamp: Date.now() });
  reply.type("text/html").send(html);
});

fastify.get("/user/:id/chartData", async (request, reply) => {
  const { id } = request.params as { id: string };
  const user = await pg.fetchUser(id);
  if (!user) {
    reply.code(400).send("Could not get user");
    return;
  }
  reply.send(await user.chartData());
});

fastify.get("/game/:id", async (request, reply) => {
  const cache = getCache(request.url);
  if (cache) {
    return reply.type("text/html").send(cache);
  }
  const { id } = request.params as { id: string };
  const html = await web.gamePage(+id);
  htmlCache.set(request.url, { html: html, timestamp: Date.now() });
  reply.type("text/html").send(html);
});

fastify.get("/game/:id/chartData", async (request, reply) => {
  const { id } = request.params as { id: number };
  const game = await pg.fetchGame(id);
  if (!game) {
    reply.code(400).send("Could not get game");
    return;
  }
  reply.send(await game.chartData());
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
