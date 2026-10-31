<script setup lang="ts">
import { computed } from "vue";
import { Bar, Line } from "vue-chartjs";
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  Filler,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";

ChartJS.register(
  BarElement,
  CategoryScale,
  Filler,
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
      pointRadius: 0,
      fill: props.kind === "line",
    },
  ],
}));

const options = computed(() => ({
  responsive: true,
  aspectRatio: props.aspectRatio,
  indexAxis: props.horizontal ? ("y" as const) : ("x" as const),
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
    y: { beginAtZero: true, ticks: { precision: 0 } },
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
