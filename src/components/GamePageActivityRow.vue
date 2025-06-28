<script setup lang="ts">
import { ref } from "vue";
import type { Activity } from "../models/models";
import GameCover from "./Games/GameCover.vue";
import Platform from "./Platforms/PlatformComp.vue";
import { formatDuration, timeAgo } from "../utils";
import DiscordAvatar from "./DiscordAvatar.vue";
import DurationComponent from "./DurationBadge.vue";
import PlatformBadge from "./Platforms/PlatformBadge.vue";
import CalendarBadge from "./CalendarBadge.vue";

const props = withDefaults(
  defineProps<{ activity: Activity; showExpand?: boolean }>(),
  {
    showExpand: false,
  }
);
const expanded = ref(false);

function toggleExpand() {
  expanded.value = !expanded.value;
}
</script>

<template>
  <div
    class="row align-items-center mb-2"
    :title="'Activity ID ' + activity.id"
  >
    <div class="col">
      <DiscordAvatar :user="activity.user" />
    </div>
    <div class="col text-start">
      <a :href="`/user/${activity.user.id}`">{{ activity.user.name }}</a>
    </div>

    <div class="col text-start">
      <PlatformBadge :platform="activity.platform" :showName="true" />
      <br />
      <DurationComponent :activity="activity" />
      <br />
      <CalendarBadge :activity="activity" />
    </div>
  </div>
  <hr />
</template>

<style scoped></style>
