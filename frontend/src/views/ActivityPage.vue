<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { formatDuration, iso8601Date } from "../utils";
import GameCover from "../components/Games/GameCover.vue";
import type {
  Activity,
  Game,
  GameWithStats,
  Platform,
  User,
  UserWithStats,
} from "../api.models";
import { TimeplayedAPI } from "../api.client";
import CalendarBasic from "../components/CalendarBasic.vue";

const route = useRoute();
const activity = ref<Activity>();
const user = ref<User>();
const game = ref<Game>();
const platform = ref<Platform>();
const error = ref("");

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
  <div v-if="activity">
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
                  >{{ user.name }}</a
                >
                <span v-else>Loading...</span>
              </li>

              <li class="list-group-item">
                <CalendarBasic :date="activity.timestamp" :absolute="true" />
              </li>
              <li
                class="list-group-item"
                :title="activity.seconds + ' seconds'"
              >
                <i class="bi bi-stopwatch"></i> 
                {{ formatDuration(activity.seconds, true) }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div v-if="error">
    <p class="text-muted">{{ error }}</p>
  </div>
</template>
