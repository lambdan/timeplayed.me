<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { formatDuration } from "../utils";
import { usePageTitle } from "../composables/usePageTitle";
import { heatBadgeStyle } from "../utils.heat";
import GameCover from "../components/Games/GameCover.vue";
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
const deleting = ref(false);
const deleted = ref(false);

function canDeleteActivity() {
  return (
    !!token.value &&
    !!activity.value &&
    !!authenticatedUser.value &&
    authenticatedUser.value.id === activity.value.user_id
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
    <div class="card p-0">
      <h1 class="card-header">#{{ activity.id }}</h1>
      <div class="card-body">
        <div class="row">
          <div class="col-md-2 text-center">
            <GameCover :gameId="activity.game_id" :size="128" />
          </div>
          <div class="col">
            <ul class="mt-4 list-group">
              <li class="list-group-item">
                <i class="bi bi-joystick"></i> 
                <a
                  class="text-decoration-none"
                  :href="'/game/' + activity.game_id"
                  v-if="game"
                  >{{ game.name }}</a
                >
                <span v-else>Loading...</span>
              </li>

              <li class="list-group-item">
                <i class="bi bi-controller"></i> 
                <span
                  v-if="editingPlatform"
                  class="d-inline-flex flex-wrap gap-2 align-items-center"
                >
                  <select
                    v-model="newPlatformId"
                    class="form-select form-select-sm w-auto"
                    aria-label="Platform"
                  >
                    <option v-for="p in platforms" :key="p.id" :value="p.id">
                      {{ p.display_name }}
                    </option>
                  </select>
                  <button
                    class="btn btn-sm btn-primary"
                    :disabled="
                      savingPlatform || newPlatformId === activity.platform_id
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
                </span>
                <template v-else>
                  <a
                    class="text-decoration-none"
                    :href="'/platform/' + activity.platform_id"
                    v-if="platform"
                    >{{ platform.display_name }}</a
                  >
                  <span v-else>Loading...</span>
                  <button
                    v-if="canDeleteActivity()"
                    class="btn btn-sm btn-link py-0 ms-1"
                    title="Change platform"
                    aria-label="Change platform"
                    @click="editPlatform"
                  >
                    <i class="bi bi-pencil"></i>
                  </button>
                </template>
              </li>

              <li class="list-group-item">
                <i class="bi bi-person"></i> 
                <a
                  class="text-decoration-none"
                  :href="'/user/' + user.id"
                  v-if="user"
                  >{{ user.display_name }}</a
                >
                <span v-else>Loading...</span>
              </li>

              <li class="list-group-item">
                <CalendarBasic
                  :date="activity.started"
                  :absolute="true"
                  :showIcon="true"
                />
                 
                <i class="bi bi-arrow-right"></i>
                 
                <CalendarBasic
                  :date="activity.ended"
                  :absolute="true"
                  :showIcon="true"
                />
              </li>

              <li
                class="list-group-item"
                :title="activity.seconds + ' seconds'"
              >
                <i class="bi bi-stopwatch"></i> 
                <!-- colored by length, same as activity rows and the recap heatmap -->
                <span
                  class="badge fw-semibold"
                  :style="{
                    ...heatBadgeStyle(activity.seconds),
                    fontVariantNumeric: 'tabular-nums',
                  }"
                  >{{ formatDuration(activity.seconds, true) }}</span
                >
              </li>
            </ul>

            <div
              v-if="canDeleteActivity()"
              class="mt-3 d-flex justify-content-end"
            >
              <button
                class="btn"
                :class="deleteArmed ? 'btn-danger' : 'btn-outline-danger'"
                :disabled="deleting"
                @click="deleteCurrentActivity"
              >
                <i class="bi bi-trash"></i>
                {{
                  deleting
                    ? "Deleting..."
                    : deleteArmed
                      ? "Click again to confirm delete"
                      : "Delete activity"
                }}
              </button>
            </div>
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
