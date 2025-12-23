<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { iso8601Date } from "../utils";
import DiscordAvatar from "../components/DiscordAvatar.vue";
import GameCover from "../components/Games/GameCover.vue";
import type { Activity, GameWithStats, UserWithStats } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import type LoadingBarVue from "../components/LoadingBar.vue";

const route = useRoute();
const activity = ref<Activity>();
const user = ref<UserWithStats>();
const game = ref<GameWithStats>();

onMounted(async () => {
  const activityId = parseInt(route.params.id as string);
  activity.value = await TimeplayedAPI.getActivity(activityId);
  if (activity.value && activity.value.user && activity.value.game) {
    user.value = await TimeplayedAPI.getUser(activity.value.user.id);
    game.value = await TimeplayedAPI.getGame(activity.value.game.id);
  }
});
</script>

<template>
  <div v-if="activity && user && game">
    <code>{{ JSON.stringify(activity) }}</code>
    <br />
    <br />
    <code>{{ JSON.stringify(user) }}</code>
    <br />
    <br />
    <code>{{ JSON.stringify(game) }}</code>
  </div>
</template>
