<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { formatDuration } from "../utils";
import GameCover from "../components/Games/GameCover.vue";
import { useApiToken } from "../composables/useApiToken";
import { useAuthenticatedUser } from "../composables/useAuthenticatedUser";
import type {
  Activity,
  Game,
  Platform,
  User,
} from "../api.models";
import { TimeplayedAPI } from "../api.client";
import CalendarBasic from "../components/CalendarBasic.vue";

const route = useRoute();
const { token } = useApiToken();
const { authenticatedUser } = useAuthenticatedUser();
const activity = ref<Activity>();
const user = ref<User>();
const game = ref<Game>();
const platform = ref<Platform>();
const error = ref("");
const deleteArmed = ref(false);
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

async function deleteCurrentActivity() {
  const currentToken = token.value;
  if (!activity.value || !currentToken || !canDeleteActivity() || deleting.value) {
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
                <a
                  class="text-decoration-none"
                  :href="'/platform/' + activity.platform_id"
                  v-if="platform"
                  >{{ platform.display_name }}</a
                >
                <span v-else>Loading...</span>
                {{ activity.emulated ? "(Emulated)" : "" }}
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
                {{ formatDuration(activity.seconds, true) }}
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
  <div v-else-if="deleted" class="alert alert-success">
    Activity deleted.
  </div>
  <div v-if="error">
    <p class="text-muted">{{ error }}</p>
  </div>
</template>
