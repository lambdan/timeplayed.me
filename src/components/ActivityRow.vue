<script setup lang="ts">
import { ref } from "vue";
import type { Activity } from "../models/models";
import GameCover from "./Games/GameCover.vue";
import Platform from "./Platforms/PlatformComp.vue";
import { formatDuration, timeAgo } from "../utils";
import DiscordAvatar from "./DiscordAvatar.vue";

const props = withDefaults(
  defineProps<{ activity: Activity; showExpand?: boolean }>(),
  {
    showExpand: false,
  }
);

const isGamePage = window.location.pathname.startsWith("/game/");
const isUserPage = window.location.pathname.startsWith("/user/");
const expanded = ref(false);

function toggleExpand() {
  expanded.value = !expanded.value;
}
</script>

<template>
  <tr class="align-middle">
    <td class="col-lg-1" v-if="!isUserPage">
      <DiscordAvatar :user="activity.user" />
    </td>

    <td v-if="!isUserPage">
      <a :href="`/user/${activity.user.id}`">{{ activity.user.name }}</a>
    </td>

    <td class="col-lg-1" v-if="!isGamePage">
      <GameCover :game="activity.game" :thumb="true" />
    </td>

    <td v-if="!isGamePage">
      <a :href="`/game/${activity.game.id}`">{{ activity.game.name }}</a>
      <br />
      <small> <Platform :platform="activity.platform" /></small>
    </td>
    <td v-else>
      <Platform :platform="activity.platform" />
    </td>

    <td v-if="!expanded">
      {{ formatDuration(activity.seconds) }}
      <br />
      <small class="text-muted">{{
        timeAgo(new Date(activity.timestamp))
      }}</small>
    </td>
    <td v-else>
      <div class="d-flex flex-column">
        <span
          ><code>{{ new Date(activity.timestamp).toISOString() }}</code></span
        >
        <span>{{ activity.seconds }} seconds</span>
      </div>
    </td>

    <td>
      <small v-if="expanded" class="text-muted">
        Session ID {{ activity.id }} <br />
      </small>
      <button v-if="showExpand" @click="toggleExpand" class="btn btn-link p-0">
        <span v-if="expanded">▼</span>
        <span v-else>▶</span>
      </button>
    </td>
  </tr>
</template>
