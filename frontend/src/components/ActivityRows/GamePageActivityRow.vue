<script setup lang="ts">
import { ref } from "vue";
import type { Activity } from "../../models/models";
import DurationComponent from "../Badges/DurationBadge.vue";
import PlatformBadge from "../Badges/PlatformBadge.vue";
import CalendarBadge from "../Badges/CalendarBadge.vue";
import UserColumn from "../Users/UserColumn.vue";

const props = withDefaults(
  defineProps<{ activity: Activity; showExpand?: boolean }>(),
  {
    showExpand: false,
  },
);
const expanded = ref(false);

function toggleExpand() {
  expanded.value = !expanded.value;
}
</script>

<template>
  <div class="row align-items-center p-0" :title="'Activity ID ' + activity.id">
    <UserColumn :user="activity.user" class="col-lg-3" />

    <div class="col text-center">
      <PlatformBadge :platform="activity.platform" :showName="true" />
       
      <DurationComponent :secs="activity.seconds" />
       
      <CalendarBadge :date="activity.timestamp" />
    </div>
  </div>
  <hr />
</template>

<style scoped></style>
