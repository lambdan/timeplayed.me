<script setup lang="ts">
import { ref, onMounted } from "vue";

const refRelativeMode = ref(false);
const refRelativeHours = ref<number>();
const refBefore = ref<Date | undefined>(new Date());
const refAfter = ref<Date | undefined>(new Date("2025-01-20T00:00:00Z")); // timeplayed start date

const ONE_HOUR = 60 * 60 * 1000;
const ONE_DAY = 24 * ONE_HOUR;

interface RelativeOption {
  label: string;
  milliseconds: number;
}

const RELATIVE_VALUES: RelativeOption[] = [
  //{ label: "Last hour", milliseconds: ONE_HOUR },
  //{ label: "Last 12 hours", milliseconds: ONE_HOUR * 12 },
  //{ label: "Last day", milliseconds: ONE_HOUR * 24 },
  { label: "Last 7 days", milliseconds: ONE_DAY * 7 },
  //{ label: "Last 14 days", milliseconds: ONE_DAY * 14 },
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
  //(e: "update:before", value: Date | undefined): void;
  //(e: "update:after", value: Date | undefined): void;
  (
    e: "updated:both",
    value: { before: Date | undefined; after: Date | undefined },
  ): void;
}>();

function setBoth(newBefore: Date | undefined, newAfter: Date | undefined) {
  if (refRelativeMode.value) {
    newBefore = undefined; // before is not needed for relative mode
  } else if (newBefore) {
    // inclusive date picker handling: set to end of day
    newBefore.setHours(23, 59, 59, 999);
  }
  refBefore.value = newBefore;
  if (newAfter) {
    newAfter.setHours(0, 0, 0, 0);
    refAfter.value = newAfter;
  }

  emit("updated:both", { before: newBefore, after: newAfter });
}

function iso8601(date: Date, includeTime = true): string {
  if (!includeTime) {
    return date.toISOString().slice(0, 10); // YYYY-MM-DD
  }
  const pad = (n: number) => n.toString().padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(
    date.getDate(),
  )} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

onMounted(() => {
  if (props.before && props.after) {
    refRelativeMode.value = false;
    setBoth(props.before, props.after);
  } else if (
    props.relativeDays !== undefined ||
    props.relativeHours !== undefined
  ) {
    refRelativeMode.value = true;
    if (props.relativeDays) {
      refRelativeHours.value = 24 * props.relativeDays;
    } else {
      refRelativeHours.value = props.relativeHours;
    }
    //setBefore(undefined);
    setBoth(
      undefined,
      new Date(Date.now() - refRelativeHours.value! * ONE_HOUR),
    );
  } else {
    // default to all time
    refRelativeMode.value = true;
    refRelativeHours.value = 0;
    setBoth(undefined, new Date(0));
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
          :value="refAfter ? iso8601(refAfter, false) : ''"
          @change="
            setBoth(
              refBefore,
              new Date(($event.target as HTMLInputElement)?.value),
            )
          "
        />
        <span class="input-group-text">-</span>
        <input
          id="before"
          type="date"
          class="form-control"
          :value="refBefore ? iso8601(refBefore, false) : ''"
          @change="
            setBoth(
              new Date(($event.target as HTMLInputElement)?.value),
              refAfter,
            )
          "
        />
        <button
          class="btn btn-sm btn-outline-primary"
          @click="
            refRelativeMode = !refRelativeMode;
            if (refRelativeMode) {
              setBoth(
                undefined,
                new Date(
                  Date.now() -
                    (refRelativeHours ? refRelativeHours * ONE_HOUR : 0),
                ),
              );
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
              (e) => {
                const val = (e.target as HTMLSelectElement).value;
                if (val === '0') {
                  // all time
                  setBoth(undefined, new Date(0));
                } else {
                  setBoth(undefined, new Date(Date.now() - parseInt(val)));
                }
              }
            "
            :value="refRelativeHours ? refRelativeHours * ONE_HOUR : '0'"
          >
            <option
              v-for="option in RELATIVE_VALUES"
              :key="option.label"
              :value="option.milliseconds"
            >
              {{ option.label }}
            </option>
          </select>
          <button
            class="btn btn-sm btn-outline-primary"
            @click="
              refRelativeMode = !refRelativeMode;
              if (!refRelativeMode) {
                setBoth(new Date(), refAfter);
              } else {
                setBoth(undefined, undefined);
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
