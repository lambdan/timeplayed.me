<script setup lang="ts">
import { ref } from "vue";
import type { Activity } from "../../models/models";
import GameCover from "../Games/GameCover.vue";
import Platform from "../Platforms/PlatformComp.vue";
import { formatDuration, timeAgo } from "../../utils";
import DiscordAvatar from "../DiscordAvatar.vue";
import DurationComponent from "../Badges/DurationBadge.vue";
import PlatformBadge from "../Badges/PlatformBadge.vue";
import CalendarBadge from "../Badges/CalendarBadge.vue";
import UserColumn from "../Users/UserColumn.vue";

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
    <UserColumn :user="activity.user" class="col-lg-3" />

    <div class="col d-none d-lg-block col-lg-1">
      <GameCover :game="activity.game" :thumb="true" :maxHeight="100" />
    </div>

    <div class="col text-start">
      <a class="text-decoration-none" :href="`/game/${activity.game.id}`">{{
        activity.game.name
      }}</a>
      <br />
      <PlatformBadge :platform="activity.platform" :showName="true" /> 
      <DurationComponent :secs="activity.seconds" />
       
      <CalendarBadge :date="activity.timestamp" />
    </div>
  </div>
  <hr />
</template>

<style scoped></style>
