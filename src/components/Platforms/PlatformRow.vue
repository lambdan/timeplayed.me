<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { PlatformWithStats } from "../../models/models";
import PlatformBadge from "../Badges/PlatformBadge.vue";
import CalendarBadge from "../Badges/CalendarBadge.vue";
import DurationBadge from "../Badges/DurationBadge.vue";

const props = withDefaults(
  defineProps<{
    platform: PlatformWithStats;
    showLastPlayed?: boolean;
  }>(),
  {
    showLastPlayed: true,
  }
);

onMounted(async () => {});
</script>

<template>
  <div class="row align-items-center mb-2 text-center">
    <div class="col-lg-1">
      <PlatformBadge :platform="props.platform.platform" :showName="true" />
    </div>

    <div class="col">
      Last played on<br /><CalendarBadge
        :date="new Date(props.platform.last_played)"
      />
    </div>

    <div class="col">
      Playtime<br />
      <DurationBadge :secs="props.platform.total_playtime" />
      <br />
      <span class="text-muted small">
        {{ (props.platform.percent * 100).toFixed(1) }}% of total
      </span>
    </div>
  </div>
  <hr />
</template>
