<script setup lang="ts">
import { defineProps, defineEmits, ref, onMounted } from "vue";

const refRelativeMode = ref(false);
const refRelativeHours = ref<number>();
const refBefore = ref<Date|undefined>(new Date());
const refAfter = ref<Date|undefined>(new Date("2025-01-20T00:00:00Z")); // timeplayed start date

const ONE_HOUR = 60 * 60 * 1000;
const ONE_DAY = 24 * ONE_HOUR;

interface RelativeOption {
  label: string;
  milliseconds: number;
}

const RELATIVE_VALUES: RelativeOption[] = [
  //{ label: "Last hour", milliseconds: ONE_HOUR },
  //{ label: "Last 12 hours", milliseconds: ONE_HOUR * 12 },
  { label: "Last 24 hours", milliseconds: ONE_HOUR * 24 },
  { label: "Last 7 days", milliseconds: ONE_DAY * 7 },
  { label: "Last 30 days", milliseconds: ONE_DAY * 30 },
  { label: "Last 90 days", milliseconds: ONE_DAY * 90 },
  { label: "Last 180 days", milliseconds: ONE_DAY * 180 },
  { label: "Last 365 days", milliseconds: ONE_DAY * 365 },
  { label: "All time", milliseconds: 0 },
];

const props = defineProps<{
  before?: Date;
  after?: Date;
  relativeDays?: number;
  relativeHours?: number;
}>();

const emit = defineEmits<{
  (e: "update:before", value: Date|undefined): void;
  (e: "update:after", value: Date|undefined): void;
}>();

function setBefore(newBefore: Date|undefined) {
  if (refRelativeMode.value) {
    newBefore = undefined; // before is not needed for relative mode
  } else if (newBefore) {
    newBefore = roundOffDate(newBefore);
  }
  refBefore.value = newBefore;
  emit("update:before", newBefore);
}

function setAfter(newAfter: Date) {
  newAfter = roundOffDate(newAfter);
  refAfter.value = newAfter;
  emit("update:after", newAfter);
}

function roundOffDate(date: Date): Date {
  const rounded = new Date(date.getTime());
  rounded.setSeconds(0);
  rounded.setMilliseconds(0);
  //rounded.setMinutes(Math.floor(rounded.getMinutes() / 5) * 5);
  return rounded;
}

function iso8601(date: Date, includeTime = true): string {
  if (!includeTime) {
    return date.toISOString().slice(0,10); // YYYY-MM-DD
  }
  const pad = (n: number) => n.toString().padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(
    date.getDate()
  )} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

onMounted(() => {
  if (props.before && props.after) {
    refRelativeMode.value = false;
    setBefore(props.before);
    setAfter(props.after);
  } else if (props.relativeDays !== undefined || props.relativeHours !== undefined) {
    refRelativeMode.value = true;
    if (props.relativeDays) {
      refRelativeHours.value = 24 * props.relativeDays;
    } else {
      refRelativeHours.value = props.relativeHours;
    }
    setBefore(undefined);
    setAfter(new Date(Date.now() - refRelativeHours.value! * ONE_HOUR));
  } else {
    // default to all time
    refRelativeMode.value = true;
    refRelativeHours.value = 0;
    setBefore(undefined);
    setAfter(new Date(0));
  }
});
</script>

<template>
  <div class="row">
  <div class="col" v-if="!refRelativeMode">
    <!-- absolute mode: one row for both dates -->
    <div class="input-group mb-2">
    <input
      type="date"
      id="after"
      class="form-control"
      :value="refAfter ? iso8601(refAfter,false) : ''"
      @change="setAfter(new Date(($event.target as HTMLInputElement)?.value))"/>
    <span class="input-group-text">to</span>
    <input
      id="before"
      type="date"
      class="form-control"
      :value="refBefore ? iso8601(refBefore,false) : ''"
      @change="setBefore(new Date(($event.target as HTMLInputElement)?.value))"/>
    <button
      class="btn btn-sm btn-outline-primary"
      @click="
      refRelativeMode = !refRelativeMode;
      if (refRelativeMode) {
        setBefore(undefined);
      }
      "
      type="button"
      title="Switch to relative mode"
    >
      <i
      class="bi"
      :class="refRelativeMode ? 'bi-calendar-date' : 'bi-clock-history'"
      ></i>
    </button>
    </div>
  </div>
  <div class="col" v-else>
    <!-- relative mode-->
    <div class="col">
    <div class="input-group mb-2">
      <select
      class="form-select"
      @change="
        e => {
          const val = (e.target as HTMLSelectElement).value;
          if (val === '0') {
            // all time
            setAfter(new Date(0));
          } else {
            setAfter(new Date(Date.now() - parseInt(val)));
          }
          setBefore(undefined);
        }
      "
      :value="refRelativeHours ? refRelativeHours * ONE_HOUR : '0'"
      >
      <option v-for="option in RELATIVE_VALUES" :key="option.label" :value="option.milliseconds">
        {{ option.label }}
      </option>
      </select>
      <button
      class="btn btn-sm btn-outline-primary"
      @click="
        refRelativeMode = !refRelativeMode;
        if (!refRelativeMode) {
          setBefore(new Date());
        } else {
          setBefore(undefined);
        }
      "
      type="button"
      title="Switch to absolute mode"
      >
      <i
        class="bi"
        :class="refRelativeMode ? 'bi-calendar-date' : 'bi-clock-history'"
      ></i>
      </button>
    </div>
    </div>
  </div>
  </div>
</template>
