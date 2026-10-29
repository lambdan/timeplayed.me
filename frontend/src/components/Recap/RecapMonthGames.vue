<script setup lang="ts">
import { computed } from "vue";
import { Bar } from "vue-chartjs";
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  LinearScale,
  Tooltip,
  type ChartOptions,
} from "chart.js";
import type { Activity } from "../../api.models";
import { formatDuration } from "../../utils";
import { MONTHS, bsColor, type RecapGame } from "../../utils.recap";

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip);

// hours per month, split by game
const props = defineProps<{
  sessionsByDay: Activity[][];
  games: RecapGame[];
  year: number;
}>();

const data = computed(() => {
  // [game index][month] = seconds, games are most played first so they end up at the bottom
  const index = new Map(props.games.map((g, i) => [g.game_id, i]));
  const seconds = props.games.map(() => new Array(12).fill(0));
  props.sessionsByDay.forEach((sessions, day) => {
    const month = new Date(props.year, 0, 1 + day).getMonth();
    for (const a of sessions)
      seconds[index.get(a.game_id)!][month] += a.seconds;
  });
  return {
    labels: MONTHS.map((m) => m.slice(0, 3)),
    datasets: props.games.map((g, i) => ({
      label: g.name,
      // null instead of 0 so empty months don't get a tooltip
      data: seconds[i].map((s) => (s ? s / 3600 : null)),
      // spread the colors around the color wheel (golden angle) so neighbours differ
      backgroundColor: `hsl(${(i * 137.5) % 360} 65% 55%)`,
    })),
  };
});

const muted = bsColor("secondary-color");
const options: ChartOptions<"bar"> = {
  responsive: true,
  maintainAspectRatio: false,
  animation: false,
  plugins: {
    // way too many games for a legend, hover a segment to see which one it is
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx) =>
          ` ${ctx.dataset.label}: ${formatDuration(Number(ctx.raw) * 3600)}`,
      },
    },
  },
  scales: {
    x: { stacked: true, grid: { display: false }, ticks: { color: muted } },
    y: {
      stacked: true,
      ticks: { color: muted, callback: (v) => `${v}h` },
      grid: { color: bsColor("border-color-translucent") },
    },
  },
};
</script>

<template>
  <div class="border rounded bg-body-tertiary p-3">
    <div style="height: 18rem">
      <Bar :data="data" :options="options" />
    </div>
  </div>
</template>
