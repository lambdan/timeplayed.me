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
    <h1>Activity #{{ activity.id }}</h1>
    <GameCover :gameId="activity.game.id" :size="128" />
    <h2>
      <a :href="'/game/' + activity.game.id">{{ activity.game.name }}</a>
    </h2>
    <h3>
      Played by
      <a :href="'/user/' + activity.user.id">{{ activity.user.name }}</a> on
      {{ new Date(activity.timestamp).toLocaleString() }}
    </h3>
    <h4>{{ formatDuration(activity.seconds) }}</h4>
  </div>
  <div v-if="error">
    <p class="text-muted">{{ error }}</p>
  </div>
</template>
