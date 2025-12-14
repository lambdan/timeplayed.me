<script setup lang="ts">
import { onMounted, ref } from "vue";
import PlatformBadge from "../Badges/PlatformBadge.vue";
import CalendarBadge from "../Badges/CalendarBadge.vue";
import DurationBadge from "../Badges/DurationBadge.vue";
import type { PlatformWithStats } from "../../models/platform.models";

const props = withDefaults(
  defineProps<{
    platform: PlatformWithStats;
    showLastPlayed?: boolean;
    showEmpty?: boolean;
  }>(),
  {
    showLastPlayed: true,
    showEmpty: false,
  },
);

const show = ref(props.showEmpty || props.platform.totals.playtime_secs > 0);

onMounted(async () => {});
</script>

<template>
  <div class="row align-items-center mb-2 text-center" v-if="show">
    <div class="col-lg-1">
      <a
        class="text-decoration-none link-primary"
        :href="`/platforms/${props.platform.platform.id}`"
      >
        <PlatformBadge :platform="props.platform.platform" :showName="true" />
      </a>
    </div>

    <div class="col" >
      Last played on<br /><CalendarBadge v-if="props.platform.newest_activity"
        :date="new Date(props.platform.newest_activity.timestamp)"
      />
    </div>

    <div class="col">
      Playtime<br />
      <DurationBadge :secs="props.platform.totals.playtime_secs" />
      <br />
      <span class="text-muted small">
        {{ (props.platform.percent * 100).toFixed(1) }}% of total
      </span>
    </div>
  </div>
  <hr />
</template>
