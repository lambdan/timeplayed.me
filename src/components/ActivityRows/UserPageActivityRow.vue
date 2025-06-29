<script setup lang="ts">
import { ref } from "vue";
import type { Activity } from "../../models/models";
import GameCover from "../Games/GameCover.vue";
import DurationComponent from "../Badges/DurationBadge.vue";
import PlatformBadge from "../Badges/PlatformBadge.vue";
import CalendarBadge from "../Badges/CalendarBadge.vue";

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
    <div class="col col-lg-1">
      <GameCover :game="activity.game" :thumb="true" />
    </div>

    <div class="col text-start">
      <a
        class="text-decoration-none link-primary"
        :href="`/game/${activity.game.id}`"
        >{{ activity.game.name }}</a
      >
      <br />
      <PlatformBadge :platform="activity.platform" :showName="true" /> 
      <DurationComponent :secs="activity.seconds" />
       
      <CalendarBadge :date="activity.timestamp" />
    </div>
  </div>
  <hr />
</template>

<style scoped></style>
