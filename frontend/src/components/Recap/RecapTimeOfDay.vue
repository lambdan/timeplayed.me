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
import { formatDuration } from "../../utils";
import { WEEKDAYS, barOptions, bsColor, type Bucket } from "../../utils.recap";
import RecapStatTile from "./RecapStatTile.vue";
import RecapWeekGrid from "./RecapWeekGrid.vue";

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip);

const props = defineProps<{
  weekdays: Bucket[];
  hours: number[];
  weekHours: number[][];
}>();

const total = computed(() => props.hours.reduce((a, b) => a + b, 0));

function share(seconds: number): string {
  return total.value ? `${((seconds / total.value) * 100).toFixed(0)}%` : "0%";
}

function hourLabel(h: number): string {
  return `${String(h).padStart(2, "0")}:00`;
}

const topDay = computed(() => {
  let best = 0;
  props.weekdays.forEach((w, i) => {
    if (w.seconds > props.weekdays[best].seconds) best = i;
  });
  return best;
});
const peakHour = computed(() => props.hours.indexOf(Math.max(...props.hours)));
const weekend = computed(
  () => props.weekdays[5].seconds + props.weekdays[6].seconds,
);

function dataset(seconds: number[]) {
  return {
    data: seconds.map((s) => s / 3600),
    backgroundColor: bsColor("warning"),
    hoverBackgroundColor: bsColor("body-color"),
  };
}

const weekdayData = computed(() => ({
  labels: WEEKDAYS.map((d) => d.slice(0, 3)),
  datasets: [dataset(props.weekdays.map((w) => w.seconds))],
}));
const weekdayOptions = barOptions(({ dataIndex: i }) => {
  const w = props.weekdays[i];
  return `${formatDuration(w.seconds)} · ${w.sessions} sessions · ${share(w.seconds)}`;
});

const hourData = computed(() => ({
  labels: props.hours.map((_, h) => String(h).padStart(2, "0")),
  datasets: [dataset(props.hours)],
}));
const hourOptions = barOptions(
  ({ dataIndex: h }) =>
    `${formatDuration(props.hours[h])} · ${share(props.hours[h])}`,
);
</script>

<template>
  <div class="row g-3">
    <div class="col-12 col-md-4">
      <RecapStatTile label="Peak hour" :value="hourLabel(peakHour)" />
    </div>
    <div class="col-12 col-md-4">
      <RecapStatTile label="Top weekday" :value="WEEKDAYS[topDay]" />
    </div>
    <div class="col-12 col-md-4">
      <RecapStatTile
        label="Weekends"
        :value="share(weekend)"
        :sub="formatDuration(weekend)"
      />
    </div>

    <div class="col-12">
      <RecapWeekGrid :weekHours="weekHours" />
    </div>

    <div class="col-12 col-md-5">
      <div class="border rounded bg-body-tertiary p-3">
        <div class="small text-uppercase fw-semibold text-body-secondary mb-2">
          Weekday
        </div>
        <div style="height: 14rem">
          <Bar :data="weekdayData" :options="weekdayOptions" />
        </div>
      </div>
    </div>
    <div class="col-12 col-md-7">
      <div class="border rounded bg-body-tertiary p-3">
        <div class="small text-uppercase fw-semibold text-body-secondary mb-2">
          Hour of day
        </div>
        <div style="height: 14rem">
          <Bar :data="hourData" :options="hourOptions" />
        </div>
      </div>
    </div>
  </div>
</template>
