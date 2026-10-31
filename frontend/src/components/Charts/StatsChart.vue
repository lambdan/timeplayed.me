<script setup lang="ts">
import { computed } from "vue";
import { Bar, Line } from "vue-chartjs";
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";

ChartJS.register(
  BarElement,
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
);

// one series in a card, for the stats page
const props = withDefaults(
  defineProps<{
    title: string;
    labels: string[];
    values: number[];
    kind?: "bar" | "line";
    /** shown after the value when hovering, like "hours" */
    unit?: string;
    /** one color, or one per bar */
    color?: string | string[];
    /** bars going sideways, for long labels like platform names */
    horizontal?: boolean;
    /** width / height, wider for charts across the whole page */
    aspectRatio?: number;
    /** data isn't in yet */
    loading?: boolean;
  }>(),
  {
    kind: "bar",
    unit: "",
    color: "rgba(158, 194, 73, 0.9)",
    horizontal: false,
    aspectRatio: 2,
    loading: false,
  },
);

const data = computed(() => ({
  labels: props.labels,
  datasets: [
    {
      data: props.values,
      backgroundColor: props.color,
      borderColor: props.color,
      // no dots on the line, only on the month you hover
      pointRadius: 0,
      pointHoverRadius: 5,
      // no fill, a total that stays flat for long would be a solid block
      fill: false,
      borderWidth: 2,
    },
  ],
}));

const options = computed(() => ({
  responsive: true,
  aspectRatio: props.aspectRatio,
  indexAxis: props.horizontal ? ("y" as const) : ("x" as const),
  // hovering anywhere above a month shows it, no need to hit the line or bar exactly
  interaction: { mode: "index" as const, intersect: false },
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (context: any) => {
          const value = props.horizontal ? context.parsed.x : context.parsed.y;
          return `${Math.round(value).toLocaleString("en")} ${props.unit}`;
        },
      },
    },
  },
  scales: {
    x: { grid: { display: false }, beginAtZero: true },
    // a bit of room above the highest value, so lines don't run along the top edge
    y: { beginAtZero: true, grace: "10%", ticks: { precision: 0 } },
  },
}));
</script>

<template>
  <div class="card p-0">
    <h2 class="card-header h4">{{ title }}</h2>
    <div class="card-body">
      <div v-if="loading" class="text-center">
        <div class="spinner-border spinner-border-sm" role="status"></div>
      </div>
      <Line v-else-if="kind === 'line'" :data="data" :options="options" />
      <Bar v-else :data="data" :options="options" />
    </div>
  </div>
</template>
