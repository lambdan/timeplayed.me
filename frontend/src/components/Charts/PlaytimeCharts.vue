<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { Game, Platform, User } from "../../api.models";
import { TimeplayedAPI } from "../../api.client";
import {
  hoursPerMonth,
  hoursPerWeekday,
  monthLabel,
  monthsSince,
  totalOverTime,
  toDays,
  WEEKDAYS,
  type DaySeconds,
} from "../../utils.stats";
import StatsChart from "./StatsChart.vue";

// total playtime over time, with playtime per month and per weekday under it, for a game, user or platform page
const props = defineProps<{
  game?: Game;
  /** with game: also its child games */
  includeChildren?: boolean;
  user?: User;
  platform?: Platform;
  /** with platform: also its child platforms */
  includeChildPlatforms?: boolean;
}>();

const days = ref<DaySeconds[]>([]);
const loading = ref(true);

let latest = 0;
watch(
  () => [props.includeChildren, props.includeChildPlatforms],
  async () => {
    const request = ++latest;
    loading.value = true;
    const byDay = await TimeplayedAPI.getChartsPlaytimeByDay({
      game: props.game?.id,
      include_children: props.includeChildren,
      user: props.user?.id,
      platform: props.platform?.id,
      include_child_platforms: props.includeChildPlatforms,
    });
    if (request !== latest) return; // toggled again meanwhile
    days.value = toDays(byDay);
    loading.value = false;
  },
  { immediate: true },
);

const months = computed(() => {
  if (days.value.length === 0) return [];
  return monthsSince(days.value[0].day);
});
const total = computed(() =>
  totalOverTime(months.value, hoursPerMonth(days.value, months.value)),
);
</script>

<template>
  <div class="row g-4">
    <div class="col-12">
      <StatsChart
        title="Total playtime"
        kind="line"
        :loading="loading"
        :labels="total.labels"
        :values="total.totals"
        unit="hours"
        :aspectRatio="4"
      />
    </div>
    <div class="col-lg-6">
      <StatsChart
        title="Playtime per month"
        :loading="loading"
        :labels="months.map(monthLabel)"
        :values="hoursPerMonth(days, months)"
        unit="hours"
      />
    </div>
    <div class="col-lg-6">
      <StatsChart
        title="Playtime per weekday"
        :loading="loading"
        :labels="WEEKDAYS"
        :values="hoursPerWeekday(days)"
        unit="hours"
      />
    </div>
  </div>
</template>
