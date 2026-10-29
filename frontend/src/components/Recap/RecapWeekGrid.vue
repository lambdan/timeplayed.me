<script setup lang="ts">
import { computed, ref } from "vue";
import { formatDuration } from "../../utils";
import { WEEKDAYS } from "../../utils.recap";

// playtime per weekday and hour of day
const props = defineProps<{ weekHours: number[][] }>();

const LEVEL_CLASSES = [
  "bg-body-secondary",
  "bg-warning bg-opacity-25",
  "bg-warning bg-opacity-50",
  "bg-warning bg-opacity-75",
  "bg-warning",
];

const max = computed(() => Math.max(...props.weekHours.flat(), 1));
const total = computed(() => props.weekHours.flat().reduce((a, b) => a + b, 0));

/** 0 = nothing, 1-4 relative to the busiest hour */
function level(seconds: number): number {
  return seconds ? Math.ceil((seconds / max.value) * 4) : 0;
}

const hovered = ref<{ day: number; hour: number }>();

function hourLabel(h: number): string {
  return `${String(h % 24).padStart(2, "0")}:00`;
}
</script>

<template>
  <div class="border rounded bg-body-tertiary p-3">
    <div class="small text-uppercase fw-semibold text-body-secondary mb-2">
      Weekday and hour
    </div>
    <div class="table-responsive">
      <table
        class="table table-borderless table-sm mb-0 small"
        style="
          --bs-table-bg: transparent;
          min-width: 640px;
          table-layout: fixed;
        "
        @mouseleave="hovered = undefined"
      >
        <thead>
          <tr>
            <th style="width: 3rem"></th>
            <th
              v-for="h in 24"
              :key="h"
              class="text-center fw-normal text-body-secondary p-0"
            >
              {{ (h - 1) % 3 === 0 ? String(h - 1).padStart(2, "0") : "" }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(hours, day) in weekHours" :key="day">
            <th class="fw-normal text-body-secondary py-0 pe-2">
              {{ WEEKDAYS[day].slice(0, 3) }}
            </th>
            <td v-for="(s, hour) in hours" :key="hour" class="p-0">
              <div
                class="rounded-1"
                :class="[
                  LEVEL_CLASSES[level(s)],
                  {
                    'border border-2 border-light':
                      hovered?.day === day && hovered?.hour === hour,
                  },
                ]"
                style="height: 1.1rem; margin: 1px"
                @mouseenter="hovered = { day, hour }"
              ></div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="small text-body-secondary mt-2">
      <template v-if="hovered">
        {{ WEEKDAYS[hovered.day] }} {{ hourLabel(hovered.hour) }} –
        {{ hourLabel(hovered.hour + 1) }}:
        <b class="text-body">{{
          formatDuration(weekHours[hovered.day][hovered.hour])
        }}</b>
        ·
        {{
          total
            ? ((weekHours[hovered.day][hovered.hour] / total) * 100).toFixed(1)
            : 0
        }}%
      </template>
      <template v-else>&nbsp;</template>
    </div>
  </div>
</template>
