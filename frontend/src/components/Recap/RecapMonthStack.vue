<script setup lang="ts">
import { computed } from "vue";
import { Bar } from "vue-chartjs";
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  LinearScale,
  Tooltip,
} from "chart.js";
import type { Activity } from "../../api.models";
import { formatDuration } from "../../utils";
import { MONTHS, barOptions } from "../../utils.recap";

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip);

// hours per month, stacked by game or platform or whatever `keyOf` picks
const props = defineProps<{
  title: string;
  sessionsByDay: Activity[][];
  year: number;
  /** most played first, so they end up at the bottom of each bar */
  items: { id: number; name: string; color?: string }[];
  keyOf: (a: Activity) => number;
}>();

const data = computed(() => {
  const index = new Map(props.items.map((item, i) => [item.id, i]));
  const seconds = props.items.map(() => new Array(12).fill(0));
  props.sessionsByDay.forEach((sessions, day) => {
    const month = new Date(props.year, 0, 1 + day).getMonth();
    for (const a of sessions) {
      seconds[index.get(props.keyOf(a))!][month] += a.seconds;
    }
  });
  return {
    labels: MONTHS.map((m) => m.slice(0, 3)),
    datasets: props.items.map((item, i) => ({
      label: item.name,
      // null instead of 0 so empty months don't get a tooltip
      data: seconds[i].map((s) => (s ? s / 3600 : null)),
      // no color given: spread them around the color wheel (golden angle) so neighbours differ
      backgroundColor: item.color ?? `hsl(${(i * 137.5) % 360} 65% 55%)`,
    })),
  };
});

// no legend, there can be way too many items. hover a segment to see what it is
const options = barOptions(
  (ctx) => `${ctx.dataset.label}: ${formatDuration(Number(ctx.raw) * 3600)}`,
  true,
);
</script>

<template>
  <div class="border rounded bg-body-tertiary p-3">
    <div class="small text-uppercase fw-semibold text-body-secondary mb-2">
      {{ title }}
    </div>
    <div style="height: 18rem">
      <Bar :data="data" :options="options" />
    </div>
  </div>
</template>
