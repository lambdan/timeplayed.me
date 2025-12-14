<script setup lang="ts">
import { onMounted, ref } from "vue";
import UserColumn from "./UserColumn.vue";
import CalendarBadge from "../Badges/CalendarBadge.vue";
import DurationBadge from "../Badges/DurationBadge.vue";
import type { UserWithStats } from "../../api.models";

const props = withDefaults(
  defineProps<{
    user: UserWithStats;
    showExpand?: boolean;
    showLastPlayed?: boolean;
  }>(),
  {
    showExpand: false,
    showLastPlayed: true,
  },
);

const expanded = ref(false);

function toggleExpand() {
  expanded.value = !expanded.value;
}

onMounted(async () => {});
</script>

<template>
  <div class="row align-items-center mb-2 text-center">
    <UserColumn :user="user.user" class="col-lg-3" />

    <div class="col" v-if="props.showLastPlayed && user.newest_activity">
      Last played<br /><CalendarBadge
        :date="new Date(user.newest_activity.timestamp)"
      />
    </div>

    <div class="col">
      Time played<br />
      <DurationBadge :secs="props.user.totals.playtime_secs" />
    </div>
  </div>
  <hr />
</template>
