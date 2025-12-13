<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { Activity } from "../../models/models";
import { formatDuration, timeAgo } from "../../utils";
import DiscordAvatar from "../DiscordAvatar.vue";
import GameCover from "../Games/GameCover.vue";
import PlatformBadge from "../Badges/PlatformBadge.vue";

const props = defineProps<{
  activity: Activity;
  context?: "userPage" | "gamePage" | "frontPage";
}>();

const refTimeDisplayed = ref("");
const refDateDisplayed = ref("");

function updateDate() {
  const activityDate = new Date(props.activity.timestamp);
  refDateDisplayed.value = timeAgo(activityDate, true);
}

onMounted(() => {
  refTimeDisplayed.value = formatDuration(props.activity.seconds);
  updateDate();
  setInterval(() => {
    updateDate();
  }, 1000); // Update every second
});
</script>

<template>
  <tr class="align-middle" :key="activity.id">
    <td>
      <small title="Activity ID" class="text-secondary">{{
        activity.id
      }}</small>
    </td>

    <td v-if="props.context !== 'userPage'">
      <DiscordAvatar :user="activity.user" :maxWidth="50"></DiscordAvatar>
    </td>
    <td v-if="props.context === 'userPage'">
      <GameCover
        :gameId="activity.game.id"
        :thumb="true"
        :maxHeight="50"
      ></GameCover>
    </td>

    <td v-if="props.context !== 'gamePage'">
      <a
        :href="`/game/${activity.game.id}`"
        class="link-underline link-underline-opacity-0"
        >{{ activity.game.name }}</a
      >
    </td>

    <td>
      <PlatformBadge :platform="activity.platform" />
    </td>

    <td :title="activity.seconds + ' seconds'">
      <i class="bi bi-clock-history"></i> {{ refTimeDisplayed }}
    </td>
    <td :title="new Date(activity.timestamp).toLocaleString()">
      <i class="bi bi-calendar"></i> {{ refDateDisplayed }}
    </td>
  </tr>
</template>
