<script setup lang="ts">
import type { Activity } from "../models/models";
import GameCover from "./GameCover.vue";
import Platform from "./Platform.vue";

const FALLBACK_AVATAR = "https://cdn.discordapp.com/embed/avatars/0.png";

defineProps<{ activity: Activity }>();

const isUserPage = window.location.pathname.startsWith("/user/");
</script>

<template>
  <tr class="align-middle">
    <td class="col-lg-1" v-if="!isUserPage">
      <a :href="`/user/${activity.user.id}`">
        <img
          :src="activity.user.avatar_url ?? FALLBACK_AVATAR"
          class="img-thumbnail img-fluid rounded-circle"
        />
      </a>
    </td>

    <td v-if="!isUserPage">
      <a :href="`/user/${activity.user.id}`">{{ activity.user.name }}</a>
    </td>

    <td class="col-lg-1">
      <GameCover :game="activity.game" />
    </td>

    <td>
      <a :href="`/game/${activity.game.id}`">{{ activity.game.name }}</a>
      <br />
      <small> <Platform :platform="activity.platform" /></small>
    </td>

    <td>{{ (activity.seconds / 3600).toFixed(1) }} hours</td>
    <td>{{ timeAgo(activity.timestamp) }}</td>
  </tr>
</template>

<script lang="ts">
function timeAgo(timestamp: number): string {
  const now = new Date();
  const parsedDate = new Date(timestamp);
  const seconds = Math.floor((now.getTime() - parsedDate.getTime()) / 1000);

  const intervals = [
    { label: "year", seconds: 31536000 },
    { label: "month", seconds: 2592000 },
    { label: "day", seconds: 86400 },
    { label: "hour", seconds: 3600 },
    { label: "minute", seconds: 60 },
  ];

  for (const i of intervals) {
    const count = Math.floor(seconds / i.seconds);
    if (count > 0) return `${count} ${i.label}${count !== 1 ? "s" : ""} ago`;
  }

  return "just now";
}
</script>
