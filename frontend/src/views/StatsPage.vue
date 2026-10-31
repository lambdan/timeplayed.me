<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import type { GameWithStats, Totals, UserWithStats } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import { formatDuration, iso8601Date } from "../utils";
import {
  busiest,
  daysSince,
  countPerMonth,
  monthLabel,
  monthsSince,
  runningTotal,
  secondsPerMonth,
  secondsPerWeekday,
  type DaySeconds,
} from "../utils.stats";
import StatsChart from "../components/Charts/StatsChart.vue";

const HOUR = 3600;
const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const totals = ref<Totals>();
const days = ref<DaySeconds[]>([]);
const users = ref<UserWithStats[]>([]);
const games = ref<GameWithStats[]>([]);
// each part of the page shows up as soon as its data is in, the user and game lists take the longest
const daysLoaded = ref(false);
const usersLoaded = ref(false);
const gamesLoaded = ref(false);

/** the list endpoints give at most 100 at a time */
async function everything<T>(
  page: (offset: number) => Promise<T[]>,
): Promise<T[]> {
  const out: T[] = [];
  while (true) {
    const data = await page(out.length);
    out.push(...data);
    if (data.length < 100) {
      return out;
    }
  }
}

onMounted(() => {
  TimeplayedAPI.getTotals().then((t) => {
    totals.value = t;
  });
  TimeplayedAPI.getChartsPlaytimeByDay({}).then((byDay) => {
    days.value = byDay.labels.map((day, i) => ({
      day,
      seconds: byDay.datasets[0]?.data[i] ?? 0,
    }));
    daysLoaded.value = true;
  });
  everything((offset) =>
    TimeplayedAPI.getUsersStats({ offset, limit: 100 }),
  ).then((u) => {
    users.value = u;
    usersLoaded.value = true;
  });
  everything((offset) =>
    TimeplayedAPI.getGamesStats({
      offset,
      limit: 100,
      sort: "id",
      order: "asc",
    }),
  ).then((g) => {
    games.value = g;
    gamesLoaded.value = true;
  });
});

const months = computed(() => {
  if (days.value.length === 0) return [];
  return monthsSince(days.value[0].day);
});
const monthLabels = computed(() => months.value.map(monthLabel));

const hoursPerMonth = computed(() => {
  const perMonth = secondsPerMonth(days.value);
  return months.value.map((m) => (perMonth.get(m) ?? 0) / HOUR);
});

const firstActivities = (
  list: { stats: { first_activity?: number | null } }[],
) => list.map((x) => x.stats.first_activity).filter((ts): ts is number => !!ts);

const newPlayersPerMonth = computed(() => {
  const perMonth = countPerMonth(firstActivities(users.value));
  return months.value.map((m) => perMonth.get(m) ?? 0);
});

const newGamesPerMonth = computed(() => {
  const perMonth = countPerMonth(firstActivities(games.value));
  return months.value.map((m) => perMonth.get(m) ?? 0);
});

const hoursPerWeekday = computed(() =>
  secondsPerWeekday(days.value).map((s) => s / HOUR),
);

const busiestDay = computed(() => busiest(days.value));
const busiestMonth = computed(() =>
  busiest(
    [...secondsPerMonth(days.value)].map(([month, seconds]) => ({
      month,
      seconds,
    })),
  ),
);

const daysTracked = computed(() => {
  if (days.value.length === 0) return 0;
  return daysSince(days.value[0].day);
});
const daysPlayed = computed(
  () => days.value.filter((d) => d.seconds > 0).length,
);

/** the numbers at the top, label and value (undefined while loading) */
const figures = computed(() => {
  const t = totals.value;
  const d = daysLoaded.value;
  const out: [string, string | undefined][] = [
    [
      "Time played",
      t && `${Math.round(t.seconds / HOUR).toLocaleString("en")} hours`,
    ],
    ["Activities", t?.activity_count.toLocaleString("en")],
    ["Players", t?.user_count.toLocaleString("en")],
    ["Games", t?.game_count.toLocaleString("en")],
    ["Platforms", t?.platform_count.toLocaleString("en")],
    ["Average session", t && formatDuration(t.seconds / t.activity_count)],
    ["Average per player", t && formatDuration(t.seconds / t.user_count)],
    [
      "Average per day",
      t && d ? formatDuration(t.seconds / daysTracked.value) : undefined,
    ],
    [
      "Days with activity",
      d
        ? `${daysPlayed.value.toLocaleString("en")} of ${daysTracked.value.toLocaleString("en")}`
        : undefined,
    ],
    [
      "Tracking since",
      t?.first_activity ? iso8601Date(t.first_activity) : undefined,
    ],
    [
      "Busiest day",
      busiestDay.value &&
        `${busiestDay.value.day} (${formatDuration(busiestDay.value.seconds)})`,
    ],
    [
      "Busiest month",
      busiestMonth.value &&
        `${monthLabel(busiestMonth.value.month)} (${formatDuration(busiestMonth.value.seconds)})`,
    ],
  ];
  return out;
});
</script>

<template>
  <div class="row">
    <div class="col-12 p-0 mt-4">
      <div class="card p-0">
        <h1 class="card-header">Stats</h1>
        <div class="card-body">
          <div class="row g-3">
            <div
              v-for="[label, value] in figures"
              :key="label"
              class="col-6 col-md-4 col-lg-3"
            >
              <div class="text-body-secondary small">{{ label }}</div>
              <div v-if="value" class="fs-5 fw-semibold">{{ value }}</div>
              <div v-else class="fs-5 placeholder-glow">
                <span class="placeholder col-6"></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="row">
    <div class="col-12 p-0 mt-4">
      <StatsChart
        title="Total playtime"
        :loading="!daysLoaded"
        kind="line"
        :labels="monthLabels"
        :values="runningTotal(hoursPerMonth)"
        unit="hours"
        :aspectRatio="4"
      />
    </div>
  </div>

  <div class="row mb-4">
    <div class="col-lg-6 p-0 pe-lg-4 mt-4">
      <StatsChart
        title="Playtime per month"
        :loading="!daysLoaded"
        :labels="monthLabels"
        :values="hoursPerMonth"
        unit="hours"
      />
    </div>
    <div class="col-lg-6 p-0 mt-4">
      <StatsChart
        title="Playtime per weekday"
        :loading="!daysLoaded"
        :labels="WEEKDAYS"
        :values="hoursPerWeekday"
        unit="hours"
      />
    </div>
    <div class="col-lg-6 p-0 pe-lg-4 mt-4">
      <StatsChart
        title="New players per month"
        :loading="!daysLoaded || !usersLoaded"
        :labels="monthLabels"
        :values="newPlayersPerMonth"
        unit="players"
        color="rgba(13, 110, 253, 0.8)"
      />
    </div>
    <div class="col-lg-6 p-0 mt-4">
      <StatsChart
        title="New games per month"
        :loading="!daysLoaded || !gamesLoaded"
        :labels="monthLabels"
        :values="newGamesPerMonth"
        unit="games"
        color="rgba(13, 110, 253, 0.8)"
      />
    </div>
  </div>
</template>
