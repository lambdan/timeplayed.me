<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { formatDuration, iso8601Date } from "../utils";
import GameCover from "../components/Games/GameCover.vue";
import type { Activity, GameWithStats, UserWithStats } from "../api.models";
import { TimeplayedAPI } from "../api.client";

const route = useRoute();
const activity = ref<Activity>();
const user = ref<UserWithStats>();
const game = ref<GameWithStats>();
const error = ref("");

onMounted(async () => {
  try {
    const activityId = parseInt(route.params.id as string);
    activity.value = await TimeplayedAPI.getActivity(activityId);
    if (activity.value && activity.value.user && activity.value.game) {
      user.value = await TimeplayedAPI.getUser(activity.value.user.id);
      game.value = await TimeplayedAPI.getGame(activity.value.game.id);
    }
  } catch (e: any) {
    error.value = e.detail || JSON.stringify(e) || "Error";
  }
});
</script>

<template>
  <div v-if="activity && user && game">
    <div class="card p-0">
      <h1 class="card-header">#{{ activity.id }}</h1>
      <div class="card-body">
        <div class="row">
          <div class="col-md-2 text-center">
            <GameCover :gameId="activity.game.id" :size="128" />
          </div>
          <div class="col">
            <ul class="mt-4 list-group">
              <li class="list-group-item">
                <i class="bi bi-joystick"></i> 
                <a
                  class="text-decoration-none"
                  :href="'/game/' + activity.game.id"
                  >{{ activity.game.name }}</a
                >
              </li>

              <li class="list-group-item">
                <i class="bi bi-controller"></i> 
                <a
                  class="text-decoration-none"
                  :href="'/platform/' + activity.platform.id"
                  >{{
                    activity.platform.name || activity.platform.abbreviation
                  }}</a
                >
              </li>

              <li class="list-group-item">
                <i class="bi bi-person"></i> 
                <a
                  class="text-decoration-none"
                  :href="'/user/' + activity.user.id"
                  >{{ activity.user.name }}</a
                >
              </li>

              <li
                class="list-group-item"
                :title="new Date(activity.timestamp).toUTCString()"
              >
                <i class="bi bi-calendar"></i>
                {{ new Date(activity.timestamp).toLocaleString() }}
              </li>
              <li
                class="list-group-item"
                :title="activity.seconds + ' seconds'"
              >
                <i class="bi bi-stopwatch"></i> 
                {{ formatDuration(activity.seconds) }}
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
