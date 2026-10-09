<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { formatDuration, sleep } from "../utils";
import GameCover from "../components/Games/GameCover.vue";
import { useApiToken } from "../composables/useApiToken";
import type {
  Game,
  LiveActivity,
  LiveActivityPost,
  Platform,
  User,
} from "../api.models";
import { TimeplayedAPI } from "../api.client";

interface PreviousGame {
  gameId: number;
  platformId: number;
  date: number;
}

const LAST_GAME_KEY = "mt-last-game";
const LAST_PLATFORM_KEY = "mt-last-platform";
const PREVIOUS_GAMES_KEY = "mt-previousGames";

const { token, clearApiToken } = useApiToken();
const loading = ref(false);
const liveActivity = ref<LiveActivity | null>(null);
const user = ref<User>();
const game = ref<Game>();
const platform = ref<Platform>();

const platforms = ref<Platform[]>([]);
const error = ref("");
const searchGameResults = ref<Game[]>([]);
const durationText = ref("...");
const previousGames = ref<PreviousGame[]>([]);
const sortedPreviousGames = computed(() =>
  [...previousGames.value].sort((a, b) => b.date - a.date),
);
const cachedGames = ref<Record<number, Game>>({});
const cachedPlatforms = ref<Record<number, Platform>>({});

async function addByIGDB() {
  const igdbId = prompt("Enter IGDB ID:");
  if (!igdbId || isNaN(+igdbId) || +igdbId <= 0) {
    return;
  }
  try {
    const igdbGame = await TimeplayedAPI.getGameByIGDB(+igdbId);
    setGame(igdbGame);
  } catch (err: any) {
    error.value = "Could not get game by IGDB ID, probably invalid ID?";
  }
}

/** in seconds */
function getDuration(): number {
  if (!liveActivity.value) {
    return 0;
  }
  return (Date.now() - liveActivity.value.started) / 1000;
}

function updateDurationText() {
  if (!liveActivity.value) {
    return (durationText.value = "...");
  }
  durationText.value = formatDuration(getDuration(), true);
}

function logout() {
  clearApiToken();
  user.value = undefined;
}

function setGame(g: Game) {
  game.value = g;
  console.log("Game set to", g.name);
  searchGameResults.value = [];
  const input = document.getElementById(
    "search-game-input",
  ) as HTMLInputElement;
  if (input) {
    input.value = g.name;
  }
}

let searchTimeout: number | null = null;
let lastSearchQuery = "";
let durationInterval: number | null = null;
async function searchGame(query: string) {
  if (query === lastSearchQuery) {
    return;
  }
  lastSearchQuery = query;

  if (searchTimeout) {
    clearTimeout(searchTimeout);
  }

  searchTimeout = window.setTimeout(async () => {
    if (!token.value) {
      return;
    }
    try {
      const results = await TimeplayedAPI.getGames({
        search: query,
        limit: 10,
        order: "desc",
        sort: "updated",
      });
      for (const result of results) {
        cachedGames.value[result.id] = result;
      }
      searchGameResults.value = results;
    } catch (err: any) {
      error.value =
        err.message || "An error occurred while searching for games.";
    }
  }, 300); // Debounce for 300ms
}

async function getGame(id: number | string): Promise<Game | null> {
  id = +id;
  if (cachedGames.value[id]) {
    return cachedGames.value[id];
  }
  try {
    const g = await TimeplayedAPI.getGame(id);
    cachedGames.value[id] = g;
    return g;
  } catch (err) {
    console.error("Error getting game", id, err);
    return null;
  }
}

function getGameSync(id: number | string): Game | null {
  return cachedGames.value[+id] || null;
}

function getPlatformSync(id: number | string): Platform | null {
  return cachedPlatforms.value[+id] || null;
}

async function getPlatform(id: number | string): Promise<Platform | null> {
  id = +id;
  if (cachedPlatforms.value[id]) {
    return cachedPlatforms.value[id];
  }
  try {
    const p = await TimeplayedAPI.getPlatform(id);
    cachedPlatforms.value[id] = p;
    return p;
  } catch (err) {
    console.error("Error getting platform", id, err);
    return null;
  }
}

async function getUser() {
  if (!token.value) {
    return;
  }
  try {
    user.value = await TimeplayedAPI.whoAmI(token.value);
  } catch (err: any) {
    error.value = "Authorization failed";
    logout();
  }
}

function applyGamePlatform(g: Game, p: Platform) {
  platform.value = p;
  setGame(g);
}

function selectPreviousGame(previousGame: PreviousGame) {
  const gameInfo = getGameSync(previousGame.gameId);
  const platformInfo = getPlatformSync(previousGame.platformId);

  if (!gameInfo || !platformInfo) {
    return;
  }

  applyGamePlatform(gameInfo, platformInfo);

  const startHeader = document.getElementById("start-playing-card-header");
  if (startHeader) {
    startHeader.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  } else {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

async function getLiveActivity() {
  if (!token.value) {
    return;
  }
  try {
    liveActivity.value = await TimeplayedAPI.getLiveActivity(token.value);
    if (!liveActivity.value) {
      return;
    }
    const _game = await getGame(liveActivity.value.game_id);
    const _platform = await getPlatform(liveActivity.value.platform_id);
    if (!_game || !_platform) {
      throw new Error(
        "Failed to fetch game or platform for running live activity",
      );
    }
    applyGamePlatform(_game, _platform);
  } catch (err: any) {
    error.value = err.message || "An error occurred while fetching data.";
  }
}

async function startLiveActivity() {
  error.value = "";
  if (!token.value || !game.value || !platform.value) {
    error.value = "Token, game, or platform is missing";
    return;
  }
  const postData: LiveActivityPost = {
    game_id: game.value.id,
    platform_id: platform.value.id,
  };
  const button = document.getElementById("start-live-activity-button");
  if (button) {
    button.setAttribute("disabled", "true");
    button.textContent = "Starting...";
  }
  try {
    const r = await TimeplayedAPI.startLiveActivity(token.value, postData);
    liveActivity.value = r;

    // update local previous
    localStorage.setItem(LAST_GAME_KEY, game.value.id.toString());
    localStorage.setItem(LAST_PLATFORM_KEY, platform.value.id.toString());
    addPreviousGame(game.value.id, platform.value.id);
  } catch (err: any) {
    error.value = err.message || "An error occurred while starting activity.";
    if (button) {
      button.removeAttribute("disabled");
      button.textContent = "Start";
    }
  }
}

async function stopLiveActivity() {
  if (getDuration() < 30) {
    abortLiveActivity(true).then(() => {
      error.value =
        "Activity was shorter than 30 seconds, it was aborted instead.";
    });
    return;
  }
  if (!token.value) {
    return;
  }
  try {
    // redirect to created activity
    const stopButton = document.getElementById("stop-live-activity-button");
    const abortButton = document.getElementById("abort-live-activity-button");
    if (stopButton) {
      stopButton.setAttribute("disabled", "true");
      stopButton.textContent = "Stopping...";
    }
    if (abortButton) {
      abortButton.setAttribute("disabled", "true");
    }
    const resp = await TimeplayedAPI.stopLiveActivity(token.value);
    if (stopButton && resp) {
      stopButton.textContent = "Success! Redirecting...";
      stopButton.classList.remove("btn-primary");
      stopButton.classList.add("btn-success");
      await sleep(200);
      window.location.href = "/activity/" + resp.id;
    }
  } catch (err: any) {
    console.error(err);
    error.value = err.message || "An error occurred while stopping activity.";
  }
}

let abortClicked = 0;
async function abortLiveActivity(force = false) {
  abortClicked++;

  const button = document.getElementById("abort-live-activity-button");
  if (!force) {
    if (abortClicked === 1 && button) {
      button.textContent = "Are you sure? Click again to confirm.";
      return;
    }
  }

  if (!token.value) {
    return;
  }

  try {
    if (button) {
      button.setAttribute("disabled", "true");
      button.textContent = "Aborting...";
    }
    abortClicked = 0;
    await TimeplayedAPI.abortLiveActivity(token.value);
    liveActivity.value = null;
    //await getLiveActivity();
  } catch (err: any) {
    error.value = err.message || "An error occurred while aborting activity.";
  }
}

async function getPlatforms() {
  let offset = 0;
  platforms.value = [];
  while (true) {
    const incoming = await TimeplayedAPI.getPlatforms({ offset, limit: 100 });
    platforms.value.push(...incoming);
    if (incoming.length < 100) {
      break;
    }
    offset += 100;
  }
  platforms.value.sort((a, b) => a.display_name.localeCompare(b.display_name));

  for (const p of platforms.value) {
    cachedPlatforms.value[p.id] = p;
  }

  // set platform to live activity platform or user default platform
  if (liveActivity.value) {
    platform.value = platforms.value.find(
      (p) => p.id === liveActivity.value!.platform_id,
    );
  } else if (user.value) {
    platform.value = platforms.value.find(
      (p) => p.id === user.value!.default_platform_id,
    );
  }
}

function addPreviousGame(gameId: number, platformId: number) {
  let updated = false;
  for (const pg of previousGames.value) {
    if (pg.gameId === gameId && pg.platformId === platformId) {
      pg.date = Date.now();
      updated = true;
    }
  }
  if (!updated) {
    previousGames.value.push({ gameId, platformId, date: Date.now() });
  }

  while (previousGames.value.length > 10) {
    // remove oldest
    previousGames.value.sort((a, b) => a.date - b.date);
    previousGames.value.shift();
  }

  localStorage.setItem(PREVIOUS_GAMES_KEY, JSON.stringify(previousGames.value));
  console.log("Saved previousGames", previousGames.value);
}

onMounted(async () => {
  // start updating duration text
  durationInterval = window.setInterval(() => {
    updateDurationText();
  }, 1000);
  updateDurationText();

  loading.value = true;
  await getUser();
  if (user.value) {
    await getLiveActivity();
    await getPlatforms();
  }
  loading.value = false;

  // load last used if not running
  if (!liveActivity.value) {
    const lastGameId = localStorage.getItem(LAST_GAME_KEY);
    const lastPlatformId = localStorage.getItem(LAST_PLATFORM_KEY);
    if (lastGameId) {
      const _game = await getGame(lastGameId);
      if (_game) {
        setGame(_game);
      }
    }
    if (lastPlatformId) {
      const _platform = await getPlatform(lastPlatformId);
      if (_platform) {
        platform.value = _platform;
      }
    }
  }

  // load in previous games
  const storedPreviousGames = localStorage.getItem(PREVIOUS_GAMES_KEY);
  if (storedPreviousGames) {
    const parsed = JSON.parse(storedPreviousGames) as PreviousGame[];
    if (Array.isArray(parsed)) {
      for (const pg of parsed) {
        if (pg.gameId && pg.platformId) {
          await getGame(pg.gameId);
          await getPlatform(pg.platformId);
        }
      }
    }
    previousGames.value = parsed;
  }
});

onUnmounted(() => {
  if (durationInterval) {
    clearInterval(durationInterval);
    durationInterval = null;
  }

  if (searchTimeout) {
    clearTimeout(searchTimeout);
    searchTimeout = null;
  }
});

watch(token, (nextToken) => {
  if (!nextToken) {
    user.value = undefined;
    liveActivity.value = null;
    game.value = undefined;
    platform.value = undefined;
    searchGameResults.value = [];
    error.value = "";
    return;
  }

  if (!user.value) {
    loading.value = true;
    getUser()
      .then(async () => {
        if (user.value) {
          await getLiveActivity();
          await getPlatforms();
        }
      })
      .finally(() => {
        loading.value = false;
      });
  }
});
</script>

<template>
  <div class="card p-0">
    <h1 class="card-header">Manual tracking</h1>
    <div class="card-body">
      <div v-if="error" class="alert alert-danger">
        {{ error }}
      </div>

      <div v-if="user">
        <div v-if="loading">Checking for live activity...</div>

        <div v-if="!loading">
          <div v-if="!liveActivity">
            <div class="card p-0">
              <h2 class="card-header" id="start-playing-card-header">
                Start playing
              </h2>
              <div class="card-body">
                <!-- search game -->
                <div class="input-group manual-field">
                  <div class="input-group-prepend">
                    <span class="input-group-text" id="search-game-addon"
                      ><i class="bi bi-joystick"></i
                    ></span>
                  </div>
                  <input
                    type="text"
                    id="search-game-input"
                    placeholder="Search for a game..."
                    class="form-control manual-form-control"
                    @input="
                      searchGame(
                        ($event.target && ($event.target as any).value) || '',
                      )
                    "
                  />
                </div>

                <ul
                  v-if="searchGameResults.length > 0"
                  class="dropdown-menu show w-100"
                  style="max-height: 300px; overflow-y: auto"
                >
                  <li
                    v-for="game in searchGameResults"
                    :key="game.id"
                    class="dropdown-item"
                  >
                    <a class="text-decoration-none" @click="setGame(game)">
                      <span class="text-secondary">{{ game.id }}</span
                      > 
                      {{ game.name }}
                      <span v-if="game.release_year" class="text-secondary"
                        >({{ game.release_year }})</span
                      ></a
                    >
                  </li>
                </ul>

                <div class="input-group manual-field mt-3">
                  <div class="input-group-prepend">
                    <span class="input-group-text" id="search-platform-addon"
                      ><i class="bi bi-controller"></i
                    ></span>
                  </div>
                  <select
                    v-model="platform"
                    class="form-select manual-form-control"
                    aria-label="Select platform"
                  >
                    <option disabled value="">Select a platform</option>
                    <option v-for="p in platforms" :key="p.id" :value="p">
                      {{ p.display_name }}
                    </option>
                  </select>
                </div>

                <div
                  class="btn-group mt-4 w-100 manual-button-row"
                  role="group"
                >
                  <button
                    @click="startLiveActivity"
                    class="btn btn-primary"
                    id="start-live-activity-button"
                    :disabled="!game || !platform"
                  >
                    <i class="bi bi-play-circle"></i>
                    Start
                  </button>
                  <button @click="addByIGDB" class="btn btn-secondary">
                    <i class="bi bi-plus-circle"></i>
                    <span class="d-none d-sm-inline">Add game by IGDB ID</span>
                    <span class="d-inline d-sm-none">Add by IGDB ID</span>
                  </button>
                </div>
                <!-- previous games -->
                <div class="mt-4" v-if="previousGames.length > 0">
                  <div
                    class="d-flex align-items-center justify-content-between mb-3"
                  >
                    <h2 class="h5 mb-0">Previous games</h2>
                    <span class="text-muted small"
                      >{{ previousGames.length }} recent</span
                    >
                  </div>

                  <div class="d-grid gap-2">
                    <div
                      v-for="previousGame in sortedPreviousGames"
                      :key="`${previousGame.gameId}-${previousGame.platformId}-${previousGame.date}`"
                      class="previous-game-item previous-game-entry"
                      role="button"
                      tabindex="0"
                      @click="selectPreviousGame(previousGame)"
                      @keydown.enter.prevent="selectPreviousGame(previousGame)"
                      @keydown.space.prevent="selectPreviousGame(previousGame)"
                    >
                      <div
                        v-if="
                          getGameSync(previousGame.gameId) &&
                          getPlatformSync(previousGame.platformId)
                        "
                        class="d-flex align-items-center justify-content-between gap-3 w-100"
                      >
                        <div
                          class="d-flex flex-column overflow-hidden min-width-0"
                        >
                          <span class="fw-semibold text-truncate">{{
                            getGameSync(previousGame.gameId)!.name
                          }}</span>
                          <small class="text-muted text-truncate">
                            {{
                              getPlatformSync(previousGame.platformId)!
                                .display_name
                            }}
                          </small>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="liveActivity">
            <div class="card p-0 manual-panel">
              <h2 class="card-header manual-card-header">Currently playing</h2>
              <div class="card-body manual-panel-body">
                <div class="row g-3 align-items-start">
                  <div class="col-md-2 text-center" v-if="game">
                    <GameCover :gameId="game.id" :size="128" />
                  </div>
                  <span v-else class="col-md-2 text-center"
                    >Loading game cover...</span
                  >

                  <div class="col">
                    <ul class="mt-2 list-group currently-list">
                      <li class="list-group-item currently-list-item">
                        <i class="bi bi-joystick"></i>
                        <a
                          class="text-decoration-none"
                          :href="'/game/' + game.id"
                          v-if="game"
                          >{{ game.name }}</a
                        >
                        <span v-else>Loading...</span>
                      </li>

                      <li class="list-group-item currently-list-item">
                        <i class="bi bi-controller"></i>
                        <a
                          class="text-decoration-none"
                          :href="'/platform/' + platform.id"
                          v-if="platform"
                          >{{ platform.display_name }}</a
                        >
                        <span v-else>Loading...</span>
                      </li>

                      <li class="list-group-item currently-list-item">
                        <i class="bi bi-stopwatch"></i>
                        <b
                          ><span id="duration" class="text-success">{{
                            durationText
                          }}</span></b
                        >
                      </li>
                    </ul>

                    <div
                      class="btn-group mt-4 w-100 manual-button-row"
                      role="group"
                      aria-label="Live activity controls"
                    >
                      <button
                        @click="stopLiveActivity"
                        class="btn btn-primary"
                        id="stop-live-activity-button"
                      >
                        <i class="bi bi-stop-circle"></i>
                        Stop
                      </button>
                      <button
                        @click="abortLiveActivity(false)"
                        class="btn btn-danger"
                        id="abort-live-activity-button"
                      >
                        <i class="bi bi-x-circle"></i>
                        Abort
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="!user" class="alert alert-secondary mt-3 mb-0">
        You need to be
        <a href="/authenticate" class="alert-link">authenticated</a>.
      </div>
    </div>
  </div>
</template>

<style scoped>
.manual-tracking-card {
  border-radius: 1rem;
}

.manual-panel {
  border: 1px solid var(--bs-border-color-translucent);
  box-shadow: none;
  overflow: hidden;
}

.manual-card-header {
  background: var(--bs-tertiary-bg);
  border-bottom: 1px solid var(--bs-border-color-translucent);
  color: var(--bs-emphasis-color);
}

.manual-panel-body {
  padding-top: 1.25rem;
}

.manual-field {
  border-radius: 0.9rem;
  overflow: hidden;
  border: 1px solid rgba(var(--bs-primary-rgb), 0.22);
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.02);
  align-items: stretch;
}

.manual-field .input-group-text {
  background: var(--bs-tertiary-bg);
  border: 0;
  color: var(--bs-secondary-color);
  padding-inline: 0.9rem;
  display: flex;
  align-items: center;
  min-height: 100%;
}

.manual-field .form-select {
  min-height: 3.125rem;
}

.manual-form-control {
  border: 0 !important;
  background: var(--bs-body-bg);
  color: var(--bs-body-color);
  box-shadow: none !important;
  min-height: 2.9rem;
}

.manual-form-control:focus {
  background: var(--bs-body-bg);
}

.manual-button-row {
  border-radius: 0.75rem;
  overflow: hidden;
}

.manual-button-row > .btn {
  flex: 1 1 0;
}

.currently-list {
  border-radius: 0.75rem;
  overflow: hidden;
}

.currently-list-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--bs-tertiary-bg);
  border-color: var(--bs-border-color-translucent);
}

.currently-list-item > i {
  color: var(--bs-secondary-color);
}

.currently-list-item + .currently-list-item {
  border-top-color: var(--bs-border-color-translucent);
}

.previous-game-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.8rem 1rem;
  border: 1px solid rgba(var(--bs-primary-rgb), 0.2);
  border-radius: 0.75rem;
  background: var(--bs-tertiary-bg);
  color: var(--bs-body-color);
  transition:
    border-color 0.2s ease,
    background 0.2s ease;
  cursor: pointer;
}

.previous-game-item:hover {
  border-color: rgba(var(--bs-primary-rgb), 0.45);
  background: rgba(var(--bs-primary-rgb), 0.12);
}

.previous-game-entry:focus-visible {
  outline: 2px solid rgba(var(--bs-primary-rgb), 0.6);
  outline-offset: 2px;
}

.previous-game-item > .d-flex {
  width: 100%;
  min-width: 0;
  flex-wrap: nowrap;
}

.min-width-0 {
  min-width: 0;
}

.text-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 576px) {
  .previous-game-item {
    padding: 0.75rem;
  }

  .previous-game-item > .d-flex {
    flex-wrap: wrap;
    gap: 0.5rem 0.75rem;
  }

  .previous-game-item .btn {
    width: 100%;
    margin-left: 0;
  }
}
</style>
