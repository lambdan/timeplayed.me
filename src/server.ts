import Fastify, { FastifyInstance } from "fastify";
import { PROD } from ".";
import { Game } from "./game";
import { Totals } from "./totals";
import { User } from "./user";
import { www } from "./www";
import { Logger } from "./logger";

const cacheAge = +(process.env.CACHE_AGE || 10 * 1000);
const cache = new Map<string, any>();
const logger = new Logger("Server");

function getCache(url: string): string | null {
  if (!PROD) {
    // annoying when developing
    return null;
  }
  if (!cache.has(url)) {
    logger.debug(url, "is not cached :(");

    return null;
  }
  logger.debug(url, "is cached!");
  return cache.get(url);
}

function cacheAndReturn(url: string, data: any): any {
  cache.set(url, data);
  setTimeout(() => {
    cache.delete(url);
    logger.debug(url, "cache expired");
  }, cacheAge);
  return data;
}

export class server {
  private fastify: FastifyInstance;
  constructor() {
    this.fastify = Fastify({ logger: true });
    // Routes
    this.fastify.get("/", async (request, reply) => {
      const cache = getCache(request.url);
      if (cache) {
        return reply.type("text/html").send(cache);
      }

      reply
        .type("text/html")
        .send(cacheAndReturn(request.url, await www.GetInstance().frontPage()));
    });

    this.fastify.get("/news", async (request, reply) => {
      const cache = getCache(request.url);
      if (cache) {
        return reply.type("text/html").send(cache);
      }

      reply
        .type("text/html")
        .send(cacheAndReturn(request.url, await www.GetInstance().newsPage()));
    });

    /* Games */
    this.fastify.get("/game/:id", async (request, reply) => {
      const cache = getCache(request.url);
      if (cache) {
        return reply.type("text/html").send(cache);
      }
      const { id } = request.params as { id: number };

      const game = await Game.fromID(id);
      if (!game) {
        return reply.code(400).send("Could not get game");
      }

      return reply
        .type("text/html")
        .send(cacheAndReturn(request.url, await game.page()));
    });

    this.fastify.get("/game/:id/chartData", async (request, reply) => {
      const cache = getCache(request.url);
      if (cache) {
        return reply.send(cache);
      }

      const { id } = request.params as { id: number };
      const game = await Game.fromID(id);
      if (!game) {
        reply.code(400).send("Could not get game");
        return;
      }

      reply.send(cacheAndReturn(request.url, await game.chartData()));
    });

    this.fastify.get("/games", async (request, reply) => {
      const cache = getCache(request.url);
      if (cache) {
        return reply.type("text/html").send(cache);
      }

      reply
        .type("text/html")
        .send(cacheAndReturn(request.url, await www.GetInstance().gamesPage()));
    });

    this.fastify.get("/platforms", async (request, reply) => {
      const cache = getCache(request.url);
      if (cache) {
        return reply.type("text/html").send(cache);
      }

      reply
        .type("text/html")
        .send(cacheAndReturn(request.url, await www.GetInstance().platformsPage()));
    });

    /* Users */
    this.fastify.get("/users", async (request, reply) => {
      const cache = getCache(request.url);
      if (cache) {
        return reply.type("text/html").send(cache);
      }

      reply
        .type("text/html")
        .send(cacheAndReturn(request.url, await www.GetInstance().usersPage()));
    });

    this.fastify.get("/user/:id", async (request, reply) => {
      const cache = getCache(request.url);
      if (cache) {
        return reply.type("text/html").send(cache);
      }
      const { id } = request.params as { id: string };
      const user = await User.fromID(id);
      if (!user) {
        return reply.code(400).send("Could not get user");
      }

      return reply
        .type("text/html")
        .send(cacheAndReturn(request.url, await user.page()));
    });

    this.fastify.get("/user/:id/sessions", async (request, reply) => {
      const { offset } = request.query as { offset?: string };
      const offsetNum = offset ? parseInt(offset, 10) : 0;

      const cache = getCache(request.url);
      if (cache) {
        return reply.type("text/html").send(cache);
      }
      const { id } = request.params as { id: string };
      const user = await User.fromID(id);
      if (!user) {
        return reply.code(400).send("Could not get user");
      }

      return reply
        .type("text/html")
        .send(cacheAndReturn(request.url, await user.sessionsPage(offsetNum)));
    });

    this.fastify.get("/user/:id/chartData", async (request, reply) => {
      const cache = getCache(request.url);
      if (cache) {
        return reply.send(cache);
      }
      const { id } = request.params as { id: string };
      const user = await User.fromID(id);

      if (!user) {
        return reply.code(400).send("Could not get user");
      }
      return reply.send(cacheAndReturn(request.url, await user.chartData()));
    });

    /* Totals */
    this.fastify.get("/totals/chartData", async (request, reply) => {
      const cache = getCache(request.url);
      if (cache) {
        return reply.send(cache);
      }
      reply.send(
        cacheAndReturn(request.url, await Totals.GetInstance().chartData())
      );
    });

    // end of routes
  }

  async run() {
    this.fastify.listen(
      { port: +(process.env.PORT || 8000), host: "0.0.0.0" },
      (err, address) => {
        if (err) {
          logger.error("Error starting server:", err);

          process.exit(1);
        }
        logger.log(`Server is running at ${address}`);
      }
    );
  }
}
