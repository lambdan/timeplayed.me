<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { formatDuration, sleep } from "../utils";
import GameCover from "../components/Games/GameCover.vue";
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

const route = useRoute();
const TOKEN_KEY = "mt-token";
const LAST_GAME_KEY = "mt-last-game";
const LAST_PLATFORM_KEY = "mt-last-platform";
const PREVIOUS_GAMES_KEY = "mt-previousGames";

const token = ref<string | null>(localStorage.getItem(TOKEN_KEY) || null);
const loading = ref(false);
const liveActivity = ref<LiveActivity | null>(null);
const user = ref<User>();
const game = ref<Game>();
const platform = ref<Platform>();

const platforms = ref<Platform[]>([]);
const error = ref("");
const searchGameResults = ref<Game[]>([]);
const searchDropdownVisible = ref(false);
const durationText = ref("...");
const previousGames = ref<PreviousGame[]>([]);
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

function login() {
  error.value = "";
  if (token.value) {
    localStorage.setItem(TOKEN_KEY, token.value);
    getUser().then(() => {
      if (user.value) {
        getLiveActivity();
        getPlatforms();
      }
    });
  } else {
    alert("Please enter a token.");
  }
}

function logout() {
  localStorage.removeItem(TOKEN_KEY);
  token.value = null;
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
      searchGameResults.value = results;
      searchDropdownVisible.value = results.length > 0;
    } catch (err: any) {
      error.value =
        err.message || "An error occurred while searching for games.";
    }
  }, 300); // Debounce for 300ms
}

async function getGame(id: number | string): Promise<Game | null> {
  if (cachedGames.value[+id]) {
    return cachedGames.value[+id];
  }
  try {
    const g = await TimeplayedAPI.getGame(+id);
    cachedGames.value[+id] = g;
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
  if (cachedPlatforms.value[+id]) {
    return cachedPlatforms.value[+id];
  }
  try {
    const p = await TimeplayedAPI.getPlatform(+id);
    cachedPlatforms.value[+id] = p;
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
  const r = await TimeplayedAPI.startLiveActivity(token.value, postData);
  liveActivity.value = r;

  // update local previous
  localStorage.setItem(LAST_GAME_KEY, game.value.id.toString());
  localStorage.setItem(LAST_PLATFORM_KEY, platform.value.id.toString());
  addPreviousGame(game.value.id, platform.value.id);
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

  if (previousGames.value.length > 10) {
    // remove oldest
    previousGames.value.sort((a, b) => a.date - b.date);
    previousGames.value.shift();
  }

  localStorage.setItem(PREVIOUS_GAMES_KEY, JSON.stringify(previousGames.value));
  console.log("Saved previousGames", previousGames.value);
}

onMounted(async () => {
  // start updating duration text
  setInterval(() => {
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
    parsed.forEach(async (pg) => {
      await getGame(pg.gameId);
      await getPlatform(pg.platformId);
    });
    previousGames.value = parsed;
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
              <h2 class="card-header">Start playing</h2>
              <div class="card-body">
                <!-- search game -->
                <div class="input-group">
                  <div class="input-group-prepend">
                    <span class="input-group-text" id="search-game-addon"
                      ><i class="bi bi-joystick"></i
                    ></span>
                  </div>
                  <input
                    type="text"
                    id="search-game-input"
                    placeholder="Search for a game..."
                    class="form-control"
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

                <div class="input-group">
                  <div class="input-group-prepend">
                    <span class="input-group-text" id="search-platform-addon"
                      ><i class="bi bi-controller"></i
                    ></span>
                  </div>
                  <select
                    v-model="platform"
                    class="form-select"
                    aria-label="Select platform"
                  >
                    <option disabled value="">Select a platform</option>
                    <option v-for="p in platforms" :key="p.id" :value="p">
                      {{ p.display_name }}
                    </option>
                  </select>
                </div>

                <div class="btn-group mt-4">
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
                    <i class="bi bi-plus-circle"></i> Add game by IGDB ID
                  </button>
                </div>
                <!-- previous games -->
                <div class="mt-4 card p-0">
                  <h2 class="card-header">Previous Games</h2>
                  <div class="card-body">
                    <ul class="list-group">
                      <li
                        class="list-group-item"
                        v-for="previousGame in previousGames.sort(
                          /* recent first */ (a, b) => b.date - a.date,
                        )"
                        :key="previousGame.date"
                      >
                        <div
                          v-if="
                            getGameSync(previousGame.gameId) &&
                            getPlatformSync(previousGame.platformId)
                          "
                        >
                          <a
                            class="text-decoration-none"
                            :href="'/game/' + previousGame.gameId"
                            >{{ getGameSync(previousGame.gameId)!.name }}</a
                          >
                          -
                          {{
                            getPlatformSync(previousGame.platformId)!
                              .display_name
                          }}
                          -
                          <button
                            @click="
                              applyGamePlatform(
                                getGameSync(previousGame.gameId)!,
                                getPlatformSync(previousGame.platformId)!,
                              )
                            "
                          >
                            Play Again
                          </button>
                        </div>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="liveActivity">
            <div class="card p-0">
              <h2 class="card-header">Currently playing</h2>
              <div class="card-body">
                <div class="row">
                  <div class="col-md-2 text-center" v-if="game">
                    <GameCover :gameId="game.id" :size="128" />
                  </div>
                  <span v-else class="col-md-2 text-center"
                    >Loading game cover...</span
                  >

                  <div class="col">
                    <ul class="mt-4 list-group">
                      <li class="list-group-item">
                        <i class="bi bi-joystick"></i> 
                        <a
                          class="text-decoration-none"
                          :href="'/game/' + game.id"
                          v-if="game"
                          >{{ game.name }}</a
                        >
                        <span v-else>Loading...</span>
                      </li>

                      <li class="list-group-item">
                        <i class="bi bi-controller"></i> 
                        <a
                          class="text-decoration-none"
                          :href="'/platform/' + platform.id"
                          v-if="platform"
                          >{{ platform.display_name }}</a
                        >
                        <span v-else>Loading...</span>
                      </li>

                      <li class="list-group-item">
                        <i class="bi bi-stopwatch"></i> 
                        <b
                          ><span id="duration" class="text-success">{{
                            durationText
                          }}</span></b
                        >
                      </li>
                    </ul>

                    <div
                      class="btn-group"
                      role="group"
                      aria-label="Live activity controls"
                    >
                      <button
                        @click="stopLiveActivity"
                        class="btn btn-primary mt-4"
                        id="stop-live-activity-button"
                      >
                        <i class="bi bi-stop-circle"></i>
                        Stop
                      </button>
                      <button
                        @click="abortLiveActivity(false)"
                        class="btn btn-danger mt-4"
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

      <div v-if="!user">
        <div class="input-group input-group-sm">
          <input
            v-model="token"
            type="password"
            placeholder="Enter your token"
            class="form-control"
          />
          <button @click="login" class="bg-primary text-white p-2 rounded">
            Login
          </button>
        </div>
        <p class="mt-2 text-sm text-secondary">
          Get a token by sending <code>!token</code> to the bot in Discord.
        </p>
      </div>

      <div v-if="user">
        <hr />
        <p>
          Logged in as
          <a class="text-decoration-none" :href="'/user/' + user.id">{{
            user.display_name
          }}</a>
        </p>
        <button @click="logout" class="bg-danger text-white p-2 rounded">
          Logout
        </button>
      </div>
    </div>
  </div>
</template>
