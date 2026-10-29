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
import { barOptions, bsColor, type RecapGame } from "../../utils.recap";

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip);

// playtime grouped by when the games came out
const props = defineProps<{ games: RecapGame[]; year: number }>();

const dated = computed(() => props.games.filter((g) => g.release_year));
const undated = computed(() => props.games.length - dated.value.length);
const total = computed(() => dated.value.reduce((a, g) => a + g.seconds, 0));

interface Group {
  label: string;
  seconds: number;
  games: number;
  /** games are most played first, so the first one we see is the top game */
  top?: RecapGame;
}

function group(
  key: (g: RecapGame) => number,
  keys: number[],
  label: (k: number) => string,
): Group[] {
  const res = new Map<number, Group>(
    keys.map((k) => [k, { label: label(k), seconds: 0, games: 0 }]),
  );
  for (const g of dated.value) {
    const r = res.get(key(g))!;
    r.seconds += g.seconds;
    r.games += 1;
    r.top ??= g;
  }
  return [...res.values()];
}

function range(from: number, to: number, step = 1): number[] {
  return Array.from(
    { length: Math.floor((to - from) / step) + 1 },
    (_, i) => from + i * step,
  );
}

const oldest = computed(() =>
  Math.min(...dated.value.map((g) => g.release_year!)),
);
const newest = computed(() =>
  Math.max(props.year, ...dated.value.map((g) => g.release_year!)),
);

const years = computed(() =>
  group((g) => g.release_year!, range(oldest.value, newest.value), String),
);
const decades = computed(() =>
  group(
    (g) => Math.floor(g.release_year! / 10) * 10,
    range(Math.floor(oldest.value / 10) * 10, newest.value, 10),
    (d) => `${d}s`,
  ).filter((d) => d.games),
);
const maxDecade = computed(() =>
  Math.max(...decades.value.map((d) => d.seconds), 1),
);

const data = computed(() => ({
  labels: years.value.map((y) => y.label),
  datasets: [
    {
      data: years.value.map((y) => y.seconds / 3600),
      backgroundColor: bsColor("warning"),
      hoverBackgroundColor: bsColor("body-color"),
    },
  ],
}));

const options = barOptions(({ dataIndex: i }) => {
  const y = years.value[i];
  if (!y.games) return "nothing";
  return `${formatDuration(y.seconds)} · ${y.games} ${y.games === 1 ? "game" : "games"} · most played: ${y.top!.name}`;
});

function share(seconds: number): string {
  return `${((seconds / total.value) * 100).toFixed(0)}%`;
}
</script>

<template>
  <template v-if="dated.length">
    <div class="border rounded bg-body-tertiary p-3">
      <div style="height: 16rem">
        <Bar :data="data" :options="options" />
      </div>
    </div>
    <div class="table-responsive mt-3">
      <table class="table table-hover align-middle">
        <thead>
          <tr>
            <th>Decade</th>
            <th class="w-25 d-none d-md-table-cell"></th>
            <th class="text-end">Games</th>
            <th class="text-end">Played</th>
            <th class="text-end d-none d-sm-table-cell">Share</th>
            <th>Most played</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in decades" :key="d.label">
            <td class="fw-semibold">{{ d.label }}</td>
            <td class="d-none d-md-table-cell">
              <div class="progress" style="height: 6px">
                <div
                  class="progress-bar bg-warning"
                  :style="{ width: `${(d.seconds / maxDecade) * 100}%` }"
                ></div>
              </div>
            </td>
            <td class="text-end">{{ d.games }}</td>
            <td class="text-end text-nowrap">
              {{ formatDuration(d.seconds) }}
            </td>
            <td class="text-end text-body-secondary d-none d-sm-table-cell">
              {{ share(d.seconds) }}
            </td>
            <td>
              <a
                :href="`/game/${d.top!.game_id}`"
                class="link-underline link-underline-opacity-0"
                >{{ d.top!.name }}</a
              >
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>
  <p v-if="undated" class="small text-body-secondary mb-0">
    {{ undated }} of {{ games.length }} games have no release year and aren't
    included
  </p>
</template>
