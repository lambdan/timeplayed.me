<script setup lang="ts">
import { computed, ref } from "vue";
import { formatDuration } from "../../utils";

const props = defineProps<{ days: number[]; year: number }>();

// hours thresholds for the color levels (level 0 = nothing played)
const LEVELS = [0, 1, 3, 6];
const LEGEND = ["None", "< 1 h", "1-3 h", "3-6 h", "6 h +"];
const LEVEL_CLASSES = [
  "bg-body-secondary",
  "bg-warning bg-opacity-25",
  "bg-warning bg-opacity-50",
  "bg-warning bg-opacity-75",
  "bg-warning",
];

interface Cell {
  date?: Date;
  seconds: number;
  level: number;
}

function level(seconds: number): number {
  if (seconds <= 0) return 0;
  const hours = seconds / 3600;
  return LEVELS.filter((l) => hours >= l).length;
}

const firstWeekday = computed(() => {
  // monday = 0
  return (new Date(Date.UTC(props.year, 0, 1)).getUTCDay() + 6) % 7;
});

const cells = computed<Cell[]>(() => {
  const padding: Cell[] = Array.from({ length: firstWeekday.value }, () => ({
    seconds: 0,
    level: -1,
  }));
  return [
    ...padding,
    ...props.days.map((seconds, i) => ({
      date: new Date(Date.UTC(props.year, 0, 1 + i)),
      seconds,
      level: level(seconds),
    })),
  ];
});

const weeks = computed(() => Math.ceil(cells.value.length / 7));

const monthLabels = computed(() => {
  return Array.from({ length: 12 }, (_, m) => {
    const dayOfYear = Math.round(
      (Date.UTC(props.year, m, 1) - Date.UTC(props.year, 0, 1)) / 86400000,
    );
    return {
      name: new Date(Date.UTC(props.year, m, 1)).toLocaleDateString("en-US", {
        month: "short",
        timeZone: "UTC",
      }),
      week: Math.floor((dayOfYear + firstWeekday.value) / 7),
    };
  });
});

const hoveredIndex = ref<number>();
const hovered = computed(() =>
  hoveredIndex.value === undefined
    ? undefined
    : cells.value[hoveredIndex.value],
);

function dateLabel(cell: Cell): string {
  return cell.date!.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
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
          @mouseleave="hoveredIndex = undefined"
        >
          <div
            v-for="(cell, i) in cells"
            :key="i"
            class="calendar-cell rounded-1"
            :class="[
              cell.level >= 0 ? LEVEL_CLASSES[cell.level] : 'invisible',
              { 'border border-2 border-light': hoveredIndex === i },
            ]"
            @mouseenter="hoveredIndex = cell.date ? i : undefined"
          ></div>
        </div>
      </div>
    </div>
    <div class="d-flex flex-wrap align-items-center gap-1 mt-2 small">
      <div class="me-auto text-body-secondary">
        <template v-if="hovered">
          {{ dateLabel(hovered) }}:
          <b class="text-body">{{ formatDuration(hovered.seconds) }}</b>
        </template>
      </div>
      <span class="text-body-secondary me-1">Less</span>
      <span
        v-for="(label, l) in LEGEND"
        :key="label"
        class="d-inline-block rounded-1"
        :class="LEVEL_CLASSES[l]"
        style="width: 12px; height: 12px"
        :title="label"
      ></span>
      <span class="text-body-secondary ms-1">More</span>
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
