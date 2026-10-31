<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
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
const props = defineProps<{ game?: Game; user?: User; platform?: Platform }>();

const days = ref<DaySeconds[]>([]);
const loading = ref(true);

onMounted(async () => {
  const byDay = await TimeplayedAPI.getChartsPlaytimeByDay({
    game: props.game?.id,
    user: props.user?.id,
    platform: props.platform?.id,
  });
  days.value = toDays(byDay);
  loading.value = false;
});

const months = computed(() => {
  if (days.value.length === 0) return [];
  return monthsSince(days.value[0].day);
});
const total = computed(() =>
  totalOverTime(months.value, hoursPerMonth(days.value, months.value)),
);
</script>

<template>
  <div class="row">
    <div class="col-12 p-0 mt-4">
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
    <div class="col-lg-6 p-0 pe-lg-4 mt-4">
      <StatsChart
        title="Playtime per month"
        :loading="loading"
        :labels="months.map(monthLabel)"
        :values="hoursPerMonth(days, months)"
        unit="hours"
      />
    </div>
    <div class="col-lg-6 p-0 mt-4">
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
