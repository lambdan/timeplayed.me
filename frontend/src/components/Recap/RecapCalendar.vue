<script setup lang="ts">
import { computed, ref } from "vue";
import { formatDuration } from "../../utils";
import { HEAT_COLORS } from "../../utils.recap";
import type { DaySession } from "../../utils.recap";

const props = defineProps<{
  days: number[];
  daySessions: DaySession[][];
  year: number;
  gameNames: Map<number, string>;
  platformNames: Map<number, string>;
}>();

// hours thresholds for the color levels (level 0 = nothing played)
// hours thresholds for each color, a day gets the last one it reaches
const LEVELS = [0, 0.5, 1, 2, 3, 4, 6, 8];
const LEGEND = [
  "None",
  "< 30 m",
  "30 m – 1 h",
  "1 – 2 h",
  "2 – 3 h",
  "3 – 4 h",
  "4 – 6 h",
  "6 – 8 h",
  "8 h +",
];

function level(seconds: number): number {
  if (seconds <= 0) return 0;
  return LEVELS.filter((l) => seconds / 3600 >= l).length;
}

// monday = 0
const firstWeekday = computed(
  () => (new Date(props.year, 0, 1).getDay() + 6) % 7,
);
/** day of year for each cell in the grid, undefined for the padding before jan 1 */
const cells = computed(() => [
  ...Array(firstWeekday.value).fill(undefined),
  ...props.days.map((_, i) => i),
]);
const weeks = computed(() => Math.ceil(cells.value.length / 7));

const monthLabels = computed(() =>
  Array.from({ length: 12 }, (_, m) => {
    const first = new Date(props.year, m, 1);
    const dayOfYear = Math.round(
      (first.getTime() - new Date(props.year, 0, 1).getTime()) / 86400000,
    );
    return {
      name: first.toLocaleDateString("en-US", { month: "short" }),
      week: Math.floor((dayOfYear + firstWeekday.value) / 7),
    };
  }),
);

const hovered = ref<number>();
const selected = ref<number>();

function select(day: number) {
  selected.value = selected.value === day ? undefined : day;
}

function dateLabel(day: number, weekday: "short" | "long" = "short"): string {
  return new Date(props.year, 0, 1 + day).toLocaleDateString("en-US", {
    weekday,
    month: "short",
    day: "numeric",
  });
}

/** "19:18", or "Oct 22 19:18" if it's not on the selected day */
function time(ts: number): string {
  const d = new Date(ts);
  const t = d.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
  });
  const day = new Date(props.year, 0, 1 + selected.value!);
  if (d.toDateString() === day.toDateString()) return t;
  return `${d.toLocaleDateString("en-US", { month: "short", day: "numeric" })} ${t}`;
}
</script>

<template>
  <div class="border rounded bg-body-tertiary p-3">
    <div class="overflow-x-auto">
      <div class="calendar" :style="{ '--weeks': weeks }">
        <div class="calendar-grid small text-body-secondary mb-1">
          <span
            v-for="m in monthLabels"
            :key="m.name"
            class="text-nowrap"
            :style="{ gridColumn: m.week + 1, gridRow: 1 }"
            >{{ m.name }}</span
          >
        </div>
        <div
          class="calendar-grid calendar-days"
          @mouseleave="hovered = undefined"
        >
          <div
            v-for="(day, i) in cells"
            :key="i"
            class="calendar-cell rounded-1"
            :class="[
              {
                invisible: day === undefined,
                'border border-2 border-light': hovered === day,
                'border border-2 border-primary': selected === day,
              },
            ]"
            :style="{
              background: HEAT_COLORS[level(day === undefined ? 0 : days[day])],
            }"
            :role="day !== undefined && days[day] ? 'button' : undefined"
            @mouseenter="hovered = day"
            @click="day !== undefined && days[day] && select(day)"
          ></div>
        </div>
      </div>
    </div>
    <div class="d-flex flex-wrap align-items-center gap-1 mt-2 small">
      <div class="me-auto text-body-secondary">
        <template v-if="hovered !== undefined">
          {{ dateLabel(hovered) }}:
          <b class="text-body">{{ formatDuration(days[hovered]) }}</b>
        </template>
        <template v-else>Click a day to see its activities</template>
      </div>
      <span class="text-body-secondary me-1">Less</span>
      <span
        v-for="(label, l) in LEGEND"
        :key="label"
        class="d-inline-block rounded-1"
        :style="{ width: '12px', height: '12px', background: HEAT_COLORS[l] }"
        :title="label"
      ></span>
      <span class="text-body-secondary ms-1">More</span>
    </div>

    <div v-if="selected !== undefined" class="mt-3">
      <div class="d-flex align-items-center mb-2">
        <h3 class="h6 fw-bold mb-0 me-auto">
          {{ dateLabel(selected, "long") }}
          <span class="fw-normal text-body-secondary">
            · {{ formatDuration(days[selected]) }} ·
            {{ daySessions[selected].length }} activities
          </span>
        </h3>
        <button
          type="button"
          class="btn-close"
          aria-label="Close"
          @click="selected = undefined"
        ></button>
      </div>
      <div class="table-responsive">
        <table class="table table-sm table-hover mb-0 align-middle">
          <thead>
            <tr>
              <th>Time</th>
              <th>Game</th>
              <th class="d-none d-sm-table-cell">Platform</th>
              <th class="text-end">Played</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="{ activity: a, seconds } in daySessions[selected]"
              :key="a.id"
            >
              <td class="text-nowrap text-body-secondary">
                <a
                  :href="`/activity/${a.id}`"
                  class="link-secondary link-underline link-underline-opacity-0"
                  >{{ time(a.started) }} – {{ time(a.ended) }}</a
                >
              </td>
              <td>
                <a
                  :href="`/game/${a.game_id}`"
                  class="link-underline link-underline-opacity-0"
                  >{{ gameNames.get(a.game_id) }}</a
                >
              </td>
              <td class="d-none d-sm-table-cell text-body-secondary">
                {{ platformNames.get(a.platform_id) }}
              </td>
              <td class="text-end text-nowrap">
                {{ formatDuration(seconds) }}
                <!-- the activity went on past (or started before) this day -->
                <div
                  v-if="Math.round(seconds) !== a.seconds"
                  class="small text-body-secondary"
                >
                  of {{ formatDuration(a.seconds) }}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* github style grid, one column per week. no bootstrap equivalent for this */
.calendar {
  min-width: 640px;
}
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(var(--weeks), 1fr);
  gap: 3px;
}
.calendar-days {
  grid-template-rows: repeat(7, auto);
  grid-auto-flow: column;
}
.calendar-cell {
  aspect-ratio: 1;
}
</style>
