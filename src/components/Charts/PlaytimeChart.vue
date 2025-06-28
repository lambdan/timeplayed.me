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
  Filler,
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
  LinearScale,
  Filler
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
    legend: { display: true }, // Show legend for clarity
    title: {
      display: false,
      text: "Daily Playtime",
    },
    tooltip: {
      callbacks: {
        label: function (context: any) {
          const value = context.parsed.y;
          if (context.dataset.label === "Total Playtime") {
            return `${value.toFixed(2)} total hours`;
          }
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
      type: "linear" as const,
      beginAtZero: true,
      title: {
        display: true,
        text: "Hours (Daily)",
      },
      position: "left" as const,
    },
    y2: {
      type: "linear" as const,
      beginAtZero: true,
      title: {
        display: true,
        text: "Total Hours",
      },
      position: "right" as const,
      grid: {
        drawOnChartArea: false, // Only want grid lines for one axis
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

  // Set label for first dataset
  if (data.datasets.length > 0) {
    data.datasets[0].label = "Daily Playtime"; // Change this to your desired label
  }

  // Add cumulative (total) playtime line
  if (data.datasets.length > 0 && data.labels.length > 0) {
    // Assume first dataset is daily playtime
    const daily = data.datasets[0].data;
    const cumulative: number[] = [];
    let sum = 0;
    for (let i = 0; i < daily.length; i++) {
      sum += daily[i];
      cumulative.push(sum);
    }
    data.datasets.push({
      label: "Total Playtime",
      data: cumulative,
      // Style will be applied below
    });
  }

  chartData.value = {
    labels: data.labels,
    datasets: data.datasets.map((ds) => {
      if (ds.label === "Daily Playtime") {
        // Daily playtime
        return {
          ...ds,
          borderColor: "rgba(75, 192, 192, 0.9)",
          backgroundColor: "rgba(75, 192, 192, 0.2)",
          tension: 0.3,
          yAxisID: "y",
        };
      } else if (ds.label === "Total Playtime") {
        // Cumulative playtime
        return {
          ...ds,
          borderColor: "rgba(255, 99, 132, 0.7)",
          backgroundColor: "rgba(255, 99, 132, 0.1)",
          borderDash: [4, 4],
          pointRadius: 0,
          tension: 0.1,
          yAxisID: "y2",
        };
      } else {
        return ds;
      }
    }),
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
