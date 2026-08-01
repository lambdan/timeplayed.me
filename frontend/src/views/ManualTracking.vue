<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { formatDuration, iso8601Date, sleep } from "../utils";
import GameCover from "../components/Games/GameCover.vue";
import type {
  Game,
  LiveActivity,
  LiveActivityPost,
  Platform,
  User,
} from "../api.models";
import { TimeplayedAPI } from "../api.client";

const route = useRoute();

const TOKEN_KEY = "mt-token";

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

const updateDurationInterval = setInterval(updateDuration, 1000);

function updateDuration() {
  const durationElement = document.getElementById("duration");
  if (!durationElement) {
    return;
  }
  if (!liveActivity.value) {
    durationElement.textContent = "...";
    return;
  }
  durationElement.textContent = `${formatDuration(
    (Date.now() - liveActivity.value.started) / 1000,
    true,
  )}`;
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

async function getLiveActivity() {
  if (!token.value) {
    return;
  }
  try {
    liveActivity.value = await TimeplayedAPI.getLiveActivity(token.value);
    if (liveActivity.value) {
      game.value = await TimeplayedAPI.getGame(liveActivity.value.game_id);
      platform.value = platforms.value.find(
        (p) => p.id === liveActivity.value?.platform_id,
      );
    }
  } catch (err: any) {
    error.value = err.message || "An error occurred while fetching data.";
  }
}

async function startLiveActivity() {
  if (!token.value || !game.value || !platform.value) {
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
}

async function stopLiveActivity() {
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
      await sleep(1000);
    }
    window.location.href = "/activity/" + resp.id;
  } catch (err: any) {
    error.value = err.message || "An error occurred while stopping activity.";
  }
}

let abortClicked = 0;
async function abortLiveActivity() {
  abortClicked++;

  const button = document.getElementById("abort-live-activity-button");
  if (abortClicked === 1 && button) {
    button.textContent = "Are you sure? Click again to confirm.";
    return;
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
    await getLiveActivity();
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

  const u = user.value;
  if (u) {
    platform.value = platforms.value.find(
      (p) => p.id === u.default_platform_id,
    );
  }
}

onMounted(async () => {
  loading.value = true;
  await getUser();
  if (user.value) {
    await getLiveActivity();
    await getPlatforms();
  }
  loading.value = false;
});
</script>
<template>
  <div class="card p-0">
    <h1 class="card-header">Manual tracking</h1>
    <div class="card-body">
      <div v-if="error" class="alert alert-danger">
        {{ error }}
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
        <p>
          <a class="text-decoration-none" :href="'/user/' + user.id"
            >Logged in as {{ user.display_name }}</a
          >.
          <a
            class="text-decoration-none text-danger"
            @click="logout"
            style="cursor: pointer"
            >Click here to logout.</a
          >
        </p>
      </div>

      <div v-if="user">
        <hr />
        <div v-if="loading">Checking for live activity...</div>

        <div v-if="!loading">
          <div v-if="!liveActivity">
            <div class="card p-0">
              <h1 class="card-header">Start playing</h1>
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

                <button
                  @click="startLiveActivity"
                  class="btn btn-primary mt-4"
                  id="start-live-activity-button"
                  :disabled="!game || !platform"
                >
                  <i class="bi bi-play-circle"></i>
                  Start
                </button>
              </div>
            </div>
          </div>

          <div v-else-if="liveActivity">
            <div class="card p-0">
              <h1 class="card-header">Currently playing</h1>
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
                          ><span id="duration" class="text-success"
                            >...</span
                          ></b
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
                        @click="abortLiveActivity"
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
    </div>
  </div>
</template>
