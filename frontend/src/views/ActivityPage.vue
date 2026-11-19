<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { formatDuration } from "../utils";
import { usePageTitle } from "../composables/usePageTitle";
import { heatBadgeStyle } from "../utils.heat";
import GameCover from "../components/Games/GameCover.vue";
import GameName from "../components/Games/GameName.vue";
import GamePicker from "../components/Games/GamePicker.vue";
import AdminEditLink from "../components/Misc/AdminEditLink.vue";
import { useApiToken } from "../composables/useApiToken";
import { useAuthenticatedUser } from "../composables/useAuthenticatedUser";
import type { Activity, Game, Platform, User } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import CalendarBasic from "../components/CalendarBasic.vue";

const route = useRoute();
const setTitle = usePageTitle();
const { token } = useApiToken();
const { authenticatedUser } = useAuthenticatedUser();
const activity = ref<Activity>();
const user = ref<User>();
const game = ref<Game>();
const platform = ref<Platform>();
const error = ref("");
const deleteArmed = ref(false);
// changing the platform, for the owner
const platforms = ref<Platform[]>([]);
const newPlatformId = ref<number>();
const savingPlatform = ref(false);
const editingPlatform = ref(false);
// changing the game, for the owner (like an emulator to the actual game)
const newGameId = ref<number | null>(null);
const newGame = ref<Game>();
const savingGame = ref(false);
const editingGame = ref(false);
const deleting = ref(false);
const deleted = ref(false);

/** the owner can delete it */
function canDeleteActivity() {
  return (
    !!token.value &&
    !!activity.value &&
    !!authenticatedUser.value &&
    authenticatedUser.value.id === activity.value.user_id
  );
}

/** changing the game or platform needs manual_activity too (the backend checks it) */
function canEditActivity() {
  return (
    canDeleteActivity() &&
    !!authenticatedUser.value?.permissions.includes("manual_activity")
  );
}

async function loadPlatforms() {
  const all: Platform[] = [];
  while (true) {
    const page = await TimeplayedAPI.getPlatforms({
      offset: all.length,
      limit: 100,
    });
    all.push(...page);
    if (page.length < 100) break;
  }
  platforms.value = all.sort((a, b) =>
    a.display_name.localeCompare(b.display_name),
  );
}

async function changePlatform() {
  if (!token.value || !activity.value || !newPlatformId.value) return;
  savingPlatform.value = true;
  error.value = "";
  try {
    activity.value = await TimeplayedAPI.setActivityPlatform(
      token.value,
      activity.value.id,
      newPlatformId.value,
    );
    platform.value = platforms.value.find(
      (p) => p.id === activity.value!.platform_id,
    );
    editingPlatform.value = false;
  } catch (e: any) {
    error.value = e?.detail || "Changing the platform failed.";
  } finally {
    savingPlatform.value = false;
  }
}

async function changeGame() {
  if (!token.value || !activity.value || !newGameId.value) return;
  savingGame.value = true;
  error.value = "";
  try {
    activity.value = await TimeplayedAPI.setActivityGame(
      token.value,
      activity.value.id,
      newGameId.value,
    );
    game.value =
      newGame.value?.id === activity.value.game_id
        ? newGame.value
        : await TimeplayedAPI.getGame(activity.value.game_id);
    editingGame.value = false;
  } catch (e: any) {
    error.value = e?.detail || "Changing the game failed.";
  } finally {
    savingGame.value = false;
  }
}

function editGame() {
  newGameId.value = activity.value?.game_id ?? null;
  editingGame.value = true;
}

// the pen next to the platform, only the owner sees it
async function editPlatform() {
  newPlatformId.value = activity.value?.platform_id;
  editingPlatform.value = true;
  if (platforms.value.length === 0) {
    await loadPlatforms();
  }
}

async function deleteCurrentActivity() {
  const currentToken = token.value;
  if (
    !activity.value ||
    !currentToken ||
    !canDeleteActivity() ||
    deleting.value
  ) {
    return;
  }

  if (!deleteArmed.value) {
    deleteArmed.value = true;
    return;
  }

  try {
    deleting.value = true;
    error.value = "";
    await TimeplayedAPI.deleteActivity(currentToken, activity.value.id);
    deleted.value = true;
  } catch (e: any) {
    error.value = e?.message || e?.detail || "Failed to delete activity.";
  } finally {
    deleting.value = false;
    deleteArmed.value = false;
  }
}

onMounted(async () => {
  try {
    const activityId = parseInt(route.params.id as string);
    activity.value = await TimeplayedAPI.getActivity(activityId);
    if (activity.value && activity.value.user_id && activity.value.game_id) {
      user.value = await TimeplayedAPI.getUser(activity.value.user_id);
      game.value = await TimeplayedAPI.getGame(activity.value.game_id);
      platform.value = await TimeplayedAPI.getPlatform(
        activity.value.platform_id,
      );

      setTitle(`Activity ${activity.value.id}`);
    }
  } catch (e: any) {
    error.value = e.detail || JSON.stringify(e) || "Error";
  }
});
</script>

<template>
  <div v-if="activity && !deleted">
    <div class="card">
      <h1 class="card-header d-flex align-items-center gap-2">
        <span class="me-auto">#{{ activity.id }}</span>
        <button
          v-if="canDeleteActivity()"
          class="btn btn-sm"
          :class="deleteArmed ? 'btn-danger' : 'btn-outline-danger'"
          :disabled="deleting"
          title="Delete activity"
          @click="deleteCurrentActivity"
        >
          <i class="bi bi-trash"></i>
          <template v-if="deleting"> Deleting...</template>
          <template v-else-if="deleteArmed"> Click again to delete</template>
        </button>
        <AdminEditLink tab="activities" :id="activity.id" />
      </h1>
      <div class="card-body">
        <div class="row g-3">
          <div class="col-12 col-sm-auto text-center">
            <!-- keyed so a changed game loads its cover -->
            <GameCover
              :key="activity.game_id"
              :gameId="activity.game_id"
              :maxHeight="200"
            />
          </div>
          <div class="col">
            <table class="table table-sm mb-0 align-middle">
              <tbody>
                <tr>
                  <!-- width 1%: only as wide as the labels -->
                  <th class="text-nowrap pe-4" style="width: 1%">Duration</th>
                  <td :title="activity.seconds + ' seconds'">
                    <!-- colored by length, same as activity rows and the recap heatmap -->
                    <span
                      class="badge fw-semibold"
                      :style="{
                        ...heatBadgeStyle(activity.seconds),
                        fontVariantNumeric: 'tabular-nums',
                      }"
                      >{{ formatDuration(activity.seconds, true) }}</span
                    >
                  </td>
                </tr>
                <tr>
                  <th class="text-nowrap pe-4">Started</th>
                  <td>
                    <CalendarBasic
                      :date="activity.started"
                      :absolute="true"
                      :showIcon="false"
                    />
                  </td>
                </tr>
                <tr>
                  <th class="text-nowrap pe-4">Ended</th>
                  <td>
                    <CalendarBasic
                      :date="activity.ended"
                      :absolute="true"
                      :showIcon="false"
                    />
                  </td>
                </tr>
                <tr>
                  <th class="text-nowrap pe-4">Game</th>
                  <td>
                    <div v-if="editingGame">
                      <GamePicker
                        v-model="newGameId"
                        size="sm"
                        class="mb-2"
                        @picked="(g) => (newGame = g as Game)"
                      />
                      <div class="d-flex gap-2">
                        <button
                          class="btn btn-sm btn-primary"
                          :disabled="
                            savingGame ||
                            !newGameId ||
                            newGameId === activity.game_id
                          "
                          @click="changeGame"
                        >
                          {{ savingGame ? "Saving..." : "Save" }}
                        </button>
                        <button
                          class="btn btn-sm btn-outline-secondary"
                          :disabled="savingGame"
                          @click="editingGame = false"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                    <div v-else class="d-flex align-items-center gap-2">
                      <a
                        :href="'/game/' + activity.game_id"
                        v-if="game"
                        class="me-auto link-underline link-underline-opacity-0"
                        ><GameName :game="game"
                      /></a>
                      <span v-else class="me-auto">Loading...</span>
                      <button
                        v-if="canEditActivity()"
                        class="btn btn-sm btn-outline-primary"
                        title="Change game"
                        aria-label="Change game"
                        @click="editGame"
                      >
                        <i class="bi bi-pencil"></i>
                      </button>
                    </div>
                  </td>
                </tr>
                <tr>
                  <th class="text-nowrap pe-4">Platform</th>
                  <td>
                    <div
                      v-if="editingPlatform"
                      class="d-flex flex-wrap gap-2 align-items-center"
                    >
                      <select
                        v-model="newPlatformId"
                        class="form-select form-select-sm w-100"
                        aria-label="Platform"
                      >
                        <option
                          v-for="p in platforms"
                          :key="p.id"
                          :value="p.id"
                        >
                          {{ p.display_name }}
                        </option>
                      </select>
                      <button
                        class="btn btn-sm btn-primary"
                        :disabled="
                          savingPlatform ||
                          newPlatformId === activity.platform_id
                        "
                        @click="changePlatform"
                      >
                        {{ savingPlatform ? "Saving..." : "Save" }}
                      </button>
                      <button
                        class="btn btn-sm btn-outline-secondary"
                        :disabled="savingPlatform"
                        @click="editingPlatform = false"
                      >
                        Cancel
                      </button>
                    </div>
                    <div v-else class="d-flex align-items-center gap-2">
                      <a
                        v-if="platform"
                        :href="'/platform/' + activity.platform_id"
                        class="me-auto link-underline link-underline-opacity-0"
                        >{{ platform.display_name }}</a
                      >
                      <span v-else class="me-auto">Loading...</span>
                      <button
                        v-if="canEditActivity()"
                        class="btn btn-sm btn-outline-primary"
                        title="Change platform"
                        aria-label="Change platform"
                        @click="editPlatform"
                      >
                        <i class="bi bi-pencil"></i>
                      </button>
                    </div>
                  </td>
                </tr>
                <tr>
                  <th class="text-nowrap pe-4">Player</th>
                  <td>
                    <a
                      :href="'/user/' + user.id"
                      v-if="user"
                      class="link-underline link-underline-opacity-0"
                      >{{ user.display_name }}</a
                    >
                    <span v-else>Loading...</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div v-else-if="deleted" class="alert alert-success">Activity deleted.</div>
  <div v-if="error">
    <p class="text-muted">{{ error }}</p>
  </div>
</template>
