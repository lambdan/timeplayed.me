<script setup lang="ts">
import { onMounted, ref } from "vue";
import { formatDuration, timeAgo } from "../../utils";
import DiscordAvatar from "../DiscordAvatar.vue";
import GameCover from "../Games/GameCover.vue";
import PlatformBadge from "../Badges/PlatformBadge.vue";
import type { Activity, User } from "../../api.models";

const props = defineProps<{
  activity?: Activity;
  user?: User;
  durationSeconds?: number;
  context?: "userPage" | "gamePage" | "frontPage";
}>();

const _id = ref<string|number>("");
const _durationSeconds = ref(0);
const _timeDisplayed = ref("");
const _dateDisplayed = ref("");

function setupActivity(activity: Activity) {
  function updateDate(d: Date) {
    _dateDisplayed.value = timeAgo(d, true);
  }
  _timeDisplayed.value = formatDuration(activity.seconds);
  updateDate(new Date(activity.timestamp));
  setInterval(() => {
    updateDate(new Date(activity.timestamp));
  }, 1000); // Update every second
}

function setupDuration() {
  if (props.durationSeconds) {
    _durationSeconds.value = props.durationSeconds;
  } else if (props.activity) {
    _durationSeconds.value = props.activity.seconds;
  } else {
    throw new Error("Either activity or duration prop must be provided");
  }
  _timeDisplayed.value = formatDuration(_durationSeconds.value);
}

onMounted(() => {
  if (props.activity) {
    _id.value = props.activity.id;
    setupActivity(props.activity);
  } else if (props.user) {
    _id.value = props.user.id;
  }

  setupDuration();
});
</script>

<template>
  <tr class="align-middle" :key="_id">
    <td v-if="props.activity">
      <small title="Activity ID" class="text-secondary">{{
        props.activity.id
      }}</small>
    </td>

    <td v-if="props.user">
      <DiscordAvatar :user="props.user" :maxWidth="50"></DiscordAvatar>
    </td>

    <td v-if="props.context !== 'userPage' && props.activity">
      <DiscordAvatar :user="props.activity.user" :maxWidth="50"></DiscordAvatar>
    </td>

    <td v-if="props.context === 'userPage' && props.activity">
      <GameCover
        :gameId="props.activity.game.id"
        :thumb="true"
        :maxHeight="50"
      ></GameCover>
    </td>

    <td v-if="props.context !== 'gamePage' && props.activity">
      <a
        :href="`/game/${props.activity.game.id}`"
        class="link-underline link-underline-opacity-0"
        >{{ props.activity.game.name }}</a
      >
    </td>

    <td v-if="props.activity">
      <PlatformBadge :platform="props.activity.platform" />
    </td>

    <td :title="`${_durationSeconds} seconds`">
      <i class="bi bi-clock-history"></i> {{ _timeDisplayed }}
    </td>

    <td
      v-if="props.activity"
      :title="new Date(props.activity.timestamp).toLocaleString()"
    >
      <i class="bi bi-calendar"></i> {{ _dateDisplayed }}
    </td>
  </tr>
</template>
