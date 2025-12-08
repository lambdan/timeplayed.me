<script setup lang="ts">
import { defineProps, defineEmits, ref, onMounted } from "vue";

const refRelativeMode = ref(false);
const refRelativeDays = ref<number|undefined>();
const refBefore = ref<Date|undefined>(new Date());
const refAfter = ref<Date|undefined>(new Date("2025-01-20T00:00:00Z")); // timeplayed start date

const ONE_DAY = 24 * 60 * 60 * 1000;

const props = defineProps<{
  before?: Date;
  after?: Date;
  relativeDays?: number;
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

function nowMinus(days: number): number {
  return Date.now() - (days * ONE_DAY);
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
  } else if (props.relativeDays !== undefined) {
    refRelativeDays.value = props.relativeDays;
    refRelativeMode.value = true;
    setBefore(undefined);
    setAfter(new Date(nowMinus(props.relativeDays!)));
  } else {
    // default to all time
    refRelativeMode.value = true;
    refRelativeDays.value = 0;
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
        let after = Date.now();
        switch ((e.target as HTMLSelectElement).value) {
          case '1':
          after -= ONE_DAY;
          break;
          case '7':
          after -= ONE_DAY * 7;
          break;
          case '30':
          after -= ONE_DAY * 30;
          break;
          case '90':
          after -= ONE_DAY * 90;
          break;
          case '365':
          after -= ONE_DAY * 365;
          break;
          default:
          after = 0; // all time
          break;
        }
        setAfter(new Date(after));
        setBefore(undefined);
        }
      "
      v-model="refRelativeDays"
      >
      <option value="1">Last day</option>
      <option value="7">Last 7 days</option>
      <option value="30">Last 30 days</option>
      <option value="90">Last 90 days</option>
      <option value="365">Last 365 days</option>
      <option value="0">All time</option>
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
