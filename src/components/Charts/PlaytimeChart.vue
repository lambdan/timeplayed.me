<script setup lang="ts">
import { ref, onMounted } from "vue";
import { Line } from "vue-chartjs";
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
} from "chart.js";
import type { Game, Platform, User } from "../../models/models";
import { sleep } from "../../utils";

ChartJS.register(
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale
);

interface ChartResponse {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
  }[];
}

const chartData = ref({
  labels: [] as string[],
  datasets: [] as any[],
});

const chartOptions = {
  responsive: true,
  plugins: {
    legend: { display: false },
    title: {
      display: false,
      text: "Daily Playtime",
    },
    tooltip: {
      callbacks: {
        label: function (context: any) {
          const value = context.parsed.y;
          return `${value.toFixed(2)} hours`;
        },
      },
    },
  },
  scales: {
    x: {
      title: {
        display: true,
        text: "Date",
      },
    },
    y: {
      beginAtZero: true,
      title: {
        display: true,
        text: "Hours",
      },
    },
  },
};

const props = withDefaults(
  defineProps<{
    user?: User;
    game?: Game;
    platform?: Platform;
  }>(),
  {
    user: undefined,
    game: undefined,
    platform: undefined,
  }
);

onMounted(async () => {
  const params = [];
  if (props.user) {
    params.push(`userId=${props.user.id}`);
  }
  if (props.game) {
    params.push(`gameId=${props.game.id}`);
  }
  if (props.platform) {
    params.push(`platform=${props.platform.id}`);
  }

  const res = await fetch(
    "/api/stats/chart/playtime_by_day?" + params.join("&")
  );

  const data = (await res.json()) as ChartResponse;

  // Turn seconds into hours
  data.datasets.forEach((dataset) => {
    dataset.data = dataset.data.map((value) => value / 3600);
  });

  // Fill in missing dates
  if (data.labels.length > 0) {
    const startDate = new Date(data.labels[0]); // First date
    const endDate = new Date(); // Today
    const allLabels: string[] = [];
    const dateMap = new Map(data.labels.map((d, i) => [d, i]));
    for (
      let d = new Date(startDate);
      d <= endDate;
      d.setDate(d.getDate() + 1)
    ) {
      const iso = d.toISOString().split("T")[0]; // YYYY-MM-DD
      allLabels.push(iso);
    }
    data.datasets = data.datasets.map((ds) => {
      const newData = allLabels.map((label) => {
        const idx = dateMap.get(label);
        return idx !== undefined ? ds.data[idx] : 0;
      });
      return { ...ds, data: newData };
    });
    data.labels = allLabels;
  }

  chartData.value = {
    labels: data.labels,
    datasets: data.datasets.map((ds) => ({
      ...ds,
      borderColor: "rgb(75, 192, 192)",
      backgroundColor: "rgba(75, 192, 192, 0.2)",
      tension: 0.3,
      fill: true,
    })),
  };
});
</script>

<template>
  <div class="p-4">
    <Line
      v-if="chartData.labels.length"
      :data="chartData"
      :options="chartOptions"
    />
    <span v-else class="spinner-border" role="status"> </span>
  </div>
</template>
