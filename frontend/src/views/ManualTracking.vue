<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { formatDuration, iso8601Date, sleep } from "../utils";
import GameCover from "../components/Games/GameCover.vue";
import type { Game, LiveActivity, Platform, User } from "../api.models";
import { TimeplayedAPI } from "../api.client";

const route = useRoute();

const token = ref<string | null>(localStorage.getItem("token"));
const loading = ref(false);
const liveActivity = ref<LiveActivity | null>(null);
const user = ref<User>();
const game = ref<Game>();
const platform = ref<Platform>();
const error = ref("");

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

function tokenSaveClick() {
  if (token.value) {
    localStorage.setItem("token", token.value);
    getUser();
  } else {
    alert("Please enter a token.");
  }
}

function tokenReset() {
  localStorage.removeItem("token");
  token.value = null;
  user.value = undefined;
}

async function getUser() {
  if (!token.value) {
    return;
  }
  user.value = await TimeplayedAPI.whoAmI(token.value);
  if (!user.value) {
    tokenReset();
  } else {
    await getLiveActivity();
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
      platform.value = await TimeplayedAPI.getPlatform(
        liveActivity.value.platform_id,
      );
    }
  } catch (err: any) {
    error.value = err.message || "An error occurred while fetching data.";
  }
}

async function stopLiveActivity() {
  if (!token.value) {
    return;
  }
  try {
    // redirect to created activity
    const button = document.getElementById("stop-live-activity-button");
    if (button) {
      button.setAttribute("disabled", "true");
      button.textContent = "Stopping...";
    }
    const resp = await TimeplayedAPI.stopLiveActivity(token.value);
    if (button && resp) {
      button.textContent = "Success! Redirecting...";
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

onMounted(async () => {
  loading.value = true;
  await getUser();
  if (user.value) {
    await getLiveActivity();
  }
  loading.value = false;
});
</script>

<template>
  <div v-if="!user">
    <input
      v-model="token"
      type="password"
      placeholder="Enter your token"
      class="border p-2 rounded w-full mb-4"
    />
    <button @click="tokenSaveClick" class="bg-primary text-white p-2 rounded">
      Save Token
    </button>
    <p class="mt-2 text-sm text-secondary">
      Get a token by sending <code>!token</code> to the bot in Discord.
    </p>
  </div>

  <div v-if="user" class="mt-4">
    <p>
      Authenticated as
      <a :href="'/user/' + user.id">{{ user.display_name }}</a>
    </p>
    <button @click="tokenReset" class="bg-danger text-white p-2 rounded mt-2">
      Logout
    </button>
  </div>

  <div v-if="user">
    <hr />
    <div v-if="loading">Loading live activity...</div>

    <div v-if="!loading">
      <div v-if="!liveActivity" class="text-secondary">
        No live activity running
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
                    <b><span id="duration" class="text-success">...</span></b>
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
</template>
