<script setup lang="ts">
import { computed, ref } from "vue";
import { Doughnut } from "vue-chartjs";
import {
  ArcElement,
  Chart as ChartJS,
  Tooltip,
  type ActiveElement,
  type ChartOptions,
} from "chart.js";
import { formatDuration } from "../../utils";
import CroppedCover from "../Games/CroppedCover.vue";
import { bsColor, type RecapPlatform } from "../../utils.recap";

ChartJS.register(ArcElement, Tooltip);

const props = defineProps<{
  platforms: RecapPlatform[];
}>();

/** index into platforms, set from both the chart and the table */
const hovered = ref<number>();
const chart = ref<{ chart?: ChartJS<"doughnut"> }>();

const data = computed(() => ({
  labels: props.platforms.map((p) => p.name),
  datasets: [
    {
      data: props.platforms.map((p) => p.seconds),
      backgroundColor: props.platforms.map((p) => p.color),
      borderColor: bsColor("tertiary-bg"),
      hoverOffset: 8,
    },
  ],
}));

const options: ChartOptions<"doughnut"> = {
  responsive: true,
  animation: false,
  cutout: "60%",
  layout: { padding: 8 },
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx) => {
          const p = props.platforms[ctx.dataIndex];
          return ` ${formatDuration(p.seconds)} (${p.percentage.toFixed(1)}%)`;
        },
      },
    },
  },
  onHover: (_, elements: ActiveElement[]) => {
    hovered.value = elements[0]?.index;
  },
};

/** hovering a table row highlights the slice */
function hoverRow(i: number | undefined) {
  hovered.value = i;
  const c = chart.value?.chart;
  if (!c) return;
  const active = i === undefined ? [] : [{ datasetIndex: 0, index: i }];
  c.setActiveElements(active);
  c.tooltip?.setActiveElements(active, { x: 0, y: 0 });
  c.update();
}
</script>

<template>
  <div class="row g-3 align-items-start">
    <div class="col-12 col-md-4">
      <div class="border rounded bg-body-tertiary p-3">
        <Doughnut ref="chart" :data="data" :options="options" />
      </div>
    </div>
    <div class="col-12 col-md-8">
      <div class="table-responsive">
        <table
          class="table table-hover align-middle mb-0"
          @mouseleave="hoverRow(undefined)"
        >
          <thead>
            <tr>
              <th>Platform</th>
              <th class="text-end">Played</th>
              <th class="text-end d-none d-sm-table-cell">Activities</th>
              <th class="text-end d-none d-sm-table-cell">Share</th>
              <!-- last like in the other tables, so the playtime isn't read as the game's -->
              <th class="text-center">Most played</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(p, i) in platforms"
              :key="p.platform_id"
              :class="{ 'table-active': hovered === i }"
              @mouseenter="hoverRow(i)"
            >
              <td class="text-nowrap">
                <span
                  class="d-inline-block rounded-circle border me-2 align-middle"
                  :style="{
                    width: '0.7rem',
                    height: '0.7rem',
                    background: p.color,
                  }"
                ></span>
                <a
                  :href="`/platform/${p.platform_id}`"
                  class="link-underline link-underline-opacity-0"
                  >{{ p.name }}</a
                >
              </td>
              <td class="text-end text-nowrap">
                {{ formatDuration(p.seconds) }}
              </td>
              <td class="text-end text-body-secondary d-none d-sm-table-cell">
                {{ p.sessions }}
              </td>
              <td class="text-end text-body-secondary d-none d-sm-table-cell">
                {{ p.percentage.toFixed(0) }}%
              </td>
              <td>
                <!-- the cover, long names made the table too wide -->
                <CroppedCover
                  :gameId="p.top_game_id"
                  class="mx-auto"
                  style="width: 32px"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
