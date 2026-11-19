<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from "vue";
import { formatDuration } from "../utils";
import GameCover from "../components/Games/GameCover.vue";
import { useApiToken } from "../composables/useApiToken";
import { useAuthenticatedUser } from "../composables/useAuthenticatedUser";
import type { Game, LiveActivity, Platform } from "../api.models";
import { TimeplayedAPI } from "../api.client";

// shorter sessions are aborted instead of saved, the backend wants at least this (MINIMUM_SESSION_LENGTH)
const MIN_SECONDS = 30;

// remembered between visits
const LAST_GAME_KEY = "mt-last-game";
const LAST_PLATFORM_KEY = "mt-last-platform";
const PREVIOUS_GAMES_KEY = "mt-previousGames";
const MODE_KEY = "mt-mode";
const MAX_PREVIOUS_GAMES = 10;

interface PreviousGame {
  gameId: number;
  platformId: number;
  date: number;
}

// start a session now, or add time already played
type Mode = "start" | "add";

function readStorage(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStorage(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    // only a convenience
  }
}

function readPreviousGames(): PreviousGame[] {
  try {
    const parsed = JSON.parse(readStorage(PREVIOUS_GAMES_KEY) ?? "[]");
    return Array.isArray(parsed)
      ? parsed.filter((pg) => pg.gameId && pg.platformId)
      : [];
  } catch {
    return [];
  }
}

const { token } = useApiToken();
const { authenticatedUser, loadingAuthenticatedUser } = useAuthenticatedUser();
// the backend checks this too, this is just so we don't show controls that won't work
const canTrack = computed(
  () => !!authenticatedUser.value?.permissions.includes("manual_activity"),
);

const loading = ref(true);
const busy = ref(false);
const error = ref("");
const mode = ref<Mode>(readStorage(MODE_KEY) === "add" ? "add" : "start");
watch(mode, (m) => writeStorage(MODE_KEY, m));

const platforms = ref<Platform[]>([]);
const platformId = ref<number>();
const platform = computed(() =>
  platforms.value.find((p) => p.id === platformId.value),
);
const game = ref<Game>();
const liveActivity = ref<LiveActivity | null>(null);

// games by id, for the previous games list and the live activity
const games = ref<Record<number, Game>>({});
async function getGame(id: number): Promise<Game | undefined> {
  if (!games.value[id]) {
    try {
      games.value[id] = await TimeplayedAPI.getGame(id);
    } catch (err) {
      console.error("Error getting game", id, err);
      return undefined;
    }
  }
  return games.value[id];
}

async function getAllPlatforms(): Promise<Platform[]> {
  const all: Platform[] = [];
  while (true) {
    const page = await TimeplayedAPI.getPlatforms({
      offset: all.length,
      limit: 100,
    });
    all.push(...page);
    if (page.length < 100) break;
  }
  return all.sort((a, b) => a.display_name.localeCompare(b.display_name));
}

// "Add played time"
const addHours = ref<number | string>("");
const addMinutes = ref<number | string>("");
const addSeconds = computed(
  () =>
    (Number(addHours.value) || 0) * 3600 + (Number(addMinutes.value) || 0) * 60,
);

// game search
const searchText = ref("");
const searchResults = ref<Game[]>([]);
let searchTimeout: number | undefined;
watch(searchText, (text) => {
  window.clearTimeout(searchTimeout);
  // the selected game's name was put in the field, nothing to search for
  if (text === game.value?.name) {
    searchResults.value = [];
    return;
  }
  // typing something else means that game isn't the one anymore
  game.value = undefined;
  if (!text.trim()) {
    searchResults.value = [];
    return;
  }
  searchTimeout = window.setTimeout(async () => {
    try {
      const results = await TimeplayedAPI.getGames({
        search: text,
        limit: 10,
        order: "desc",
        sort: "updated",
      });
      for (const g of results) {
        games.value[g.id] = g;
      }
      searchResults.value = results;
    } catch {
      error.value = "Searching for games failed";
    }
  }, 300);
});

function selectGame(g: Game) {
  game.value = g;
  searchText.value = g.name;
  searchResults.value = [];
}

async function addByIGDB() {
  const igdbId = Number(prompt("Enter IGDB ID:"));
  if (!igdbId || igdbId <= 0) return;
  try {
    selectGame(await TimeplayedAPI.getGameByIGDB(igdbId));
  } catch {
    error.value = "Could not get game by IGDB ID, probably invalid ID?";
  }
}

// previous games, most recent first
const previousGames = ref<PreviousGame[]>(readPreviousGames());
const sortedPreviousGames = computed(() =>
  [...previousGames.value].sort((a, b) => b.date - a.date),
);

/** preselected next time, and in previous games */
function remember(gameId: number, platformId: number) {
  writeStorage(LAST_GAME_KEY, gameId.toString());
  writeStorage(LAST_PLATFORM_KEY, platformId.toString());
  const others = previousGames.value.filter(
    (pg) => pg.gameId !== gameId || pg.platformId !== platformId,
  );
  previousGames.value = [{ gameId, platformId, date: Date.now() }, ...others]
    .sort((a, b) => b.date - a.date)
    .slice(0, MAX_PREVIOUS_GAMES);
  writeStorage(PREVIOUS_GAMES_KEY, JSON.stringify(previousGames.value));
}

async function selectPreviousGame(pg: PreviousGame) {
  const g = await getGame(pg.gameId);
  if (!g) return;
  selectGame(g);
  platformId.value = pg.platformId;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function errorMessage(err: any, fallback: string): string {
  return typeof err?.detail === "string" ? err.detail : fallback;
}

// elapsed time of the live activity
const now = ref(Date.now());
const timer = window.setInterval(() => (now.value = Date.now()), 1000);
onUnmounted(() => {
  window.clearInterval(timer);
  window.clearTimeout(searchTimeout);
});
const elapsedSeconds = computed(() =>
  liveActivity.value ? (now.value - liveActivity.value.started) / 1000 : 0,
);

async function start() {
  if (!token.value || !game.value || !platform.value) return;
  error.value = "";
  busy.value = true;
  try {
    liveActivity.value = await TimeplayedAPI.startLiveActivity(token.value, {
      game_id: game.value.id,
      platform_id: platform.value.id,
    });
    remember(game.value.id, platform.value.id);
  } catch (err) {
    error.value = errorMessage(err, "Starting failed");
  } finally {
    busy.value = false;
  }
}

async function add() {
  if (!token.value || !game.value || !platform.value) return;
  error.value = "";
  busy.value = true;
  try {
    const activity = await TimeplayedAPI.addActivity(token.value, {
      game_id: game.value.id,
      platform_id: platform.value.id,
      seconds: addSeconds.value,
    });
    remember(game.value.id, platform.value.id);
    window.location.href = `/activity/${activity.id}`;
  } catch (err) {
    error.value = errorMessage(err, "Adding failed");
    busy.value = false;
  }
}

async function stop() {
  if (!token.value) return;
  if (elapsedSeconds.value < MIN_SECONDS) {
    await abort();
    error.value = `Shorter than ${MIN_SECONDS} seconds, so it was aborted instead`;
    return;
  }
  error.value = "";
  busy.value = true;
  try {
    const activity = await TimeplayedAPI.stopLiveActivity(token.value);
    window.location.href = `/activity/${activity.id}`;
  } catch (err) {
    error.value = errorMessage(err, "Stopping failed");
    busy.value = false;
  }
}

// abort needs a second click
const abortArmed = ref(false);
async function abort() {
  if (!token.value) return;
  busy.value = true;
  try {
    await TimeplayedAPI.abortLiveActivity(token.value);
    liveActivity.value = null;
  } catch (err) {
    error.value = errorMessage(err, "Aborting failed");
  } finally {
    busy.value = false;
    abortArmed.value = false;
  }
}

function abortClicked() {
  if (abortArmed.value) {
    abort();
  } else {
    abortArmed.value = true;
  }
}

async function load() {
  if (!token.value) return;
  loading.value = true;
  try {
    const [live, allPlatforms] = await Promise.all([
      TimeplayedAPI.getLiveActivity(token.value),
      getAllPlatforms(),
    ]);
    platforms.value = allPlatforms;
    liveActivity.value = live ?? null;

    // the running game, or the last used one
    const gameId = live?.game_id ?? Number(readStorage(LAST_GAME_KEY));
    const g = gameId ? await getGame(gameId) : undefined;
    if (g) {
      selectGame(g);
    }
    const lastPlatformId = Number(readStorage(LAST_PLATFORM_KEY)) || undefined;
    platformId.value = live?.platform_id ?? lastPlatformId;

    for (const pg of previousGames.value) {
      getGame(pg.gameId);
    }
  } catch (err) {
    error.value = errorMessage(err, "Loading failed");
  } finally {
    loading.value = false;
  }
}

watch(
  canTrack,
  (can) => {
    if (can) {
      load();
    }
  },
  { immediate: true },
);
</script>

<template>
  <div class="card mx-auto" style="max-width: 600px">
    <h1 class="card-header">Manual tracking</h1>
    <div class="card-body">
      <div v-if="error" class="alert alert-danger">{{ error }}</div>

      <div v-if="loadingAuthenticatedUser" class="text-center">
        <div class="spinner-border" role="status"></div>
      </div>
      <p v-else-if="!authenticatedUser" class="mb-0">
        You need to be <a href="/authenticate">authenticated</a>.
      </p>
      <p v-else-if="!canTrack" class="mb-0">
        You don't have permission to use manual tracking.
      </p>
      <div v-else-if="loading" class="text-center">
        <div class="spinner-border" role="status"></div>
      </div>

      <!-- playing right now -->
      <template v-else-if="liveActivity">
        <div class="d-flex gap-3 align-items-center mb-4">
          <GameCover
            :gameId="liveActivity.game_id"
            :maxHeight="120"
            :clickable="false"
          />
          <div style="min-width: 0">
            <a
              class="d-block h5 mb-1 text-break"
              :href="`/game/${liveActivity.game_id}`"
              >{{ games[liveActivity.game_id]?.name ?? "..." }}</a
            >
            <a
              v-if="platform"
              class="d-block text-body-secondary mb-2"
              :href="`/platform/${platform.id}`"
              >{{ platform.display_name }}</a
            >
            <div class="fs-2 font-monospace text-success">
              {{ formatDuration(elapsedSeconds, true) }}
            </div>
          </div>
        </div>
        <div class="d-grid gap-2">
          <button class="btn btn-primary btn-lg" :disabled="busy" @click="stop">
            <i class="bi bi-stop-circle"></i> Stop and save
          </button>
          <button
            class="btn btn-outline-danger"
            :disabled="busy"
            @click="abortClicked"
          >
            <i class="bi bi-x-circle"></i>
            {{ abortArmed ? "Click again to abort" : "Abort" }}
          </button>
        </div>
      </template>

      <!-- start a session, or add one already played -->
      <template v-else>
        <div class="btn-group w-100 mb-3" role="group">
          <input
            id="mode-start"
            v-model="mode"
            type="radio"
            class="btn-check"
            value="start"
          />
          <label class="btn btn-outline-primary" for="mode-start"
            ><i class="bi bi-play-circle"></i> Start now</label
          >
          <input
            id="mode-add"
            v-model="mode"
            type="radio"
            class="btn-check"
            value="add"
          />
          <label class="btn btn-outline-primary" for="mode-add"
            ><i class="bi bi-stopwatch"></i> Add played time</label
          >
        </div>

        <div class="mb-3 position-relative">
          <label for="game-search" class="form-label">Game</label>
          <input
            id="game-search"
            v-model="searchText"
            type="search"
            class="form-control form-control-lg"
            placeholder="Search for a game..."
            autocomplete="off"
          />
          <div
            v-if="searchResults.length"
            class="list-group position-absolute w-100 z-3 shadow overflow-auto"
            style="max-height: 300px"
          >
            <button
              v-for="g in searchResults"
              :key="g.id"
              type="button"
              class="list-group-item list-group-item-action"
              @click="selectGame(g)"
            >
              {{ g.name }}
              <span v-if="g.release_year" class="text-body-secondary"
                >({{ g.release_year }})</span
              >
            </button>
          </div>
          <button
            type="button"
            class="btn btn-link btn-sm px-0"
            @click="addByIGDB"
          >
            Add a game by IGDB ID
          </button>
        </div>

        <div class="mb-3">
          <label for="platform" class="form-label">Platform</label>
          <select
            id="platform"
            v-model="platformId"
            class="form-select form-select-lg"
          >
            <option :value="undefined" disabled>Select a platform</option>
            <option v-for="p in platforms" :key="p.id" :value="p.id">
              {{ p.display_name }}
            </option>
          </select>
        </div>

        <div v-if="mode === 'add'" class="mb-3">
          <label for="add-hours" class="form-label">Played for</label>
          <div class="row g-2">
            <div class="col">
              <div class="input-group input-group-lg">
                <input
                  id="add-hours"
                  v-model="addHours"
                  type="number"
                  inputmode="numeric"
                  min="0"
                  class="form-control"
                  aria-label="Hours"
                />
                <span class="input-group-text">h</span>
              </div>
            </div>
            <div class="col">
              <div class="input-group input-group-lg">
                <input
                  v-model="addMinutes"
                  type="number"
                  inputmode="numeric"
                  min="0"
                  max="59"
                  class="form-control"
                  aria-label="Minutes"
                />
                <span class="input-group-text">m</span>
              </div>
            </div>
          </div>
        </div>

        <div class="d-grid">
          <button
            v-if="mode === 'start'"
            class="btn btn-primary btn-lg"
            :disabled="busy || !game || !platform"
            @click="start"
          >
            <i class="bi bi-play-circle"></i> Start
          </button>
          <button
            v-else
            class="btn btn-primary btn-lg"
            :disabled="busy || !game || !platform || addSeconds <= 0"
            @click="add"
          >
            <i class="bi bi-plus-circle"></i> Add
          </button>
        </div>

        <template v-if="sortedPreviousGames.length">
          <h2 class="h6 mt-4">Previous games</h2>
          <div class="list-group">
            <button
              v-for="pg in sortedPreviousGames"
              :key="`${pg.gameId}-${pg.platformId}`"
              type="button"
              class="list-group-item list-group-item-action"
              @click="selectPreviousGame(pg)"
            >
              <div class="fw-semibold text-truncate">
                {{ games[pg.gameId]?.name ?? "..." }}
              </div>
              <small class="text-body-secondary">{{
                platforms.find((p) => p.id === pg.platformId)?.display_name
              }}</small>
            </button>
          </div>
        </template>
      </template>
    </div>
  </div>
</template>
