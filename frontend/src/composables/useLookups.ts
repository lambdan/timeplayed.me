import { reactive } from "vue";
import { TimeplayedAPI } from "../api.client";
import type { Game, Platform, User } from "../api.models";

// shared by every row on the page, so each id is only fetched once
const users = reactive(new Map<number, User>());
const games = reactive(new Map<number, Game>());
const platforms = reactive(new Map<number, Platform>());
const requested = new Set<string>();

function once(key: string, fetch: () => Promise<unknown>) {
  if (requested.has(key)) return;
  requested.add(key);
  fetch().catch(() => requested.delete(key)); // try again next time
}

/** users/games/platforms by id, fetched (and cached) the first time they're asked for */
export function useLookups() {
  return {
    user(id: number): User | undefined {
      once(`u${id}`, () =>
        TimeplayedAPI.getUser(id).then((u) => users.set(id, u)),
      );
      return users.get(id);
    },
    game(id: number): Game | undefined {
      once(`g${id}`, () =>
        TimeplayedAPI.getGame(id).then((g) => games.set(id, g)),
      );
      return games.get(id);
    },
    platform(id: number): Platform | undefined {
      once(`p${id}`, () =>
        TimeplayedAPI.getPlatform(id).then((p) => platforms.set(id, p)),
      );
      return platforms.get(id);
    },
  };
}
