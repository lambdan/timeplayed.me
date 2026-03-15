<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import {
  endOfMonth,
  endOfWeek,
  endOfYear,
  startOfMonth,
  startOfWeek,
  startOfYear,
} from "../../utils.date";

const props = defineProps<{
  before?: Date;
  after?: Date;
  relativeMillis?: number;
  toggleable?: boolean;
}>();

const emit = defineEmits<{
  (e: "updated:both", value: EmitData): void;
}>();

// --- Constants ---

const ONE_HOUR = 60 * 60 * 1000;
const ONE_DAY = 24 * ONE_HOUR;
const DEFAULT_RELATIVE_MILLIS = ONE_DAY * 7;

/** Sentinel values for calendar-based presets (not real millisecond durations). */
const PRESET_VALUES = {
  ALL_TIME: -1,
  THIS_YEAR: -2,
  THIS_MONTH: -3,
  THIS_WEEK: -6,
  LAST_YEAR: -4,
  LAST_MONTH: -5,
  LAST_WEEK: -7,
} as const;

// --- Types ---

interface RelativeOption {
  label: string;
  value: number;
}

interface EmitData {
  before: Date | undefined;
  after: Date | undefined;
  allTime: boolean;
  relativeMode: boolean;
}

// --- Preset options ---

const PRESETS: RelativeOption[] = [
  { label: "Last 7 days", value: ONE_DAY * 7 },
  { label: "Last 30 days", value: ONE_DAY * 30 },
  { label: "Last 90 days", value: ONE_DAY * 90 },
  { label: "Last 180 days", value: ONE_DAY * 180 },
  { label: "Last 365 days", value: ONE_DAY * 365 },
  { label: "This week", value: PRESET_VALUES.THIS_WEEK },
  { label: "Last week", value: PRESET_VALUES.LAST_WEEK },
  { label: "This month", value: PRESET_VALUES.THIS_MONTH },
  { label: "Last month", value: PRESET_VALUES.LAST_MONTH },
  { label: "This year", value: PRESET_VALUES.THIS_YEAR },
  { label: "Last year", value: PRESET_VALUES.LAST_YEAR },
  { label: "All time", value: PRESET_VALUES.ALL_TIME },
];

// --- LocalStorage helpers ---

const STORAGE_KEY_VERSION = 1; // increment to invalidate stored values

function storageKey(
  what: "before" | "after" | "relativeMillis" | "mode",
): string {
  return `dateRangerPicker::${STORAGE_KEY_VERSION}::${window.location.pathname}::${what}`;
}

function loadMode(): "absolute" | "relative" | null {
  const stored = localStorage.getItem(storageKey("mode"));
  return stored === "absolute" || stored === "relative" ? stored : null;
}

function saveMode(mode: "absolute" | "relative"): void {
  localStorage.setItem(storageKey("mode"), mode);
}

function loadRelativeMillis(): number {
  const stored = localStorage.getItem(storageKey("relativeMillis"));
  if (stored !== null) {
    const val = parseInt(stored);
    if (!isNaN(val)) return val;
  }
  return props.relativeMillis ?? DEFAULT_RELATIVE_MILLIS;
}

function saveRelativeMillis(val: number): void {
  localStorage.setItem(storageKey("relativeMillis"), val.toString());
}

function loadAbsoluteDates(): { before: Date; after: Date } {
  const defaultAfter = new Date();
  defaultAfter.setUTCDate(defaultAfter.getUTCDate() - 7);
  defaultAfter.setUTCHours(0, 0, 0, 0);
  const defaultBefore = new Date();
  defaultBefore.setUTCHours(23, 59, 59, 999);

  let after = defaultAfter;
  let before = defaultBefore;

  const storedAfter = localStorage.getItem(storageKey("after"));
  if (storedAfter !== null) {
    const maybe = new Date(parseInt(storedAfter));
    if (isValidDate(maybe)) after = maybe;
  }

  const storedBefore = localStorage.getItem(storageKey("before"));
  if (storedBefore !== null) {
    const maybe = new Date(parseInt(storedBefore));
    if (isValidDate(maybe)) before = maybe;
  }

  return { before, after };
}

function saveAbsoluteDates(before: Date, after: Date): void {
  localStorage.setItem(storageKey("before"), before.getTime().toString());
  localStorage.setItem(storageKey("after"), after.getTime().toString());
}

// --- Validation ---

function isValidDate(d: unknown): d is Date {
  try {
    const date = d instanceof Date ? d : new Date(d as string | number);
    if (isNaN(date.getTime())) return false;
    const year = date.getUTCFullYear();
    return year >= 2000 && year <= 2100;
  } catch {
    return false;
  }
}

// --- State ---

const relativeMode = ref(true);
const toggleable = computed(() => props.toggleable !== false);

// Relative mode state
const selectedPreset = ref<number>(
  props.relativeMillis ?? DEFAULT_RELATIVE_MILLIS,
);

// Absolute mode state
const absoluteBefore = ref<Date | undefined>();
const absoluteAfter = ref<Date | undefined>();
const beforeInputRaw = ref("");
const afterInputRaw = ref("");
const beforeInputValid = ref(true);
const afterInputValid = ref(true);

// --- Emit with deduplication and debounce ---

let lastEmitted: string | null = null;
let debounceId = 0;

async function emitUpdate(data: EmitData): Promise<void> {
  const serialized = JSON.stringify(data);
  if (serialized === lastEmitted) return;

  debounceId++;
  const myId = debounceId;
  await new Promise<void>((resolve) => setTimeout(resolve, 400));
  if (myId !== debounceId) return;

  lastEmitted = serialized;
  emit("updated:both", data);
}

// --- Preset resolution ---

function resolveDateRange(presetValue: number): {
  before: Date | undefined;
  after: Date | undefined;
} {
  const now = new Date();
  switch (presetValue) {
    case PRESET_VALUES.ALL_TIME:
      return { before: undefined, after: undefined };

    case PRESET_VALUES.THIS_WEEK:
      return { before: endOfWeek(now), after: startOfWeek(now) };

    case PRESET_VALUES.LAST_WEEK: {
      const lastWeek = new Date(now);
      lastWeek.setUTCDate(lastWeek.getUTCDate() - 7);
      return { before: endOfWeek(lastWeek), after: startOfWeek(lastWeek) };
    }

    case PRESET_VALUES.THIS_MONTH:
      return { before: endOfMonth(now), after: startOfMonth(now) };

    case PRESET_VALUES.LAST_MONTH: {
      const lastMonth = new Date(now);
      lastMonth.setUTCMonth(lastMonth.getUTCMonth() - 1);
      return { before: endOfMonth(lastMonth), after: startOfMonth(lastMonth) };
    }

    case PRESET_VALUES.THIS_YEAR:
      return { before: endOfYear(now), after: startOfYear(now) };

    case PRESET_VALUES.LAST_YEAR: {
      const lastYear = new Date(now);
      lastYear.setUTCFullYear(lastYear.getUTCFullYear() - 1);
      return { before: endOfYear(lastYear), after: startOfYear(lastYear) };
    }

    default: {
      // Positive millisecond duration: rolling window ending now
      const after = new Date(Date.now() - presetValue);
      after.setUTCHours(0, 0, 0, 0);
      return { before: undefined, after };
    }
  }
}

// --- Relative mode ---

function applyRelativePreset(value: number): void {
  selectedPreset.value = value;
  saveRelativeMillis(value);
  const { before, after } = resolveDateRange(value);
  emitUpdate({
    before,
    after,
    relativeMode: true,
    allTime: before === undefined && after === undefined,
  });
}

// --- Absolute mode ---

function toISODate(date: Date): string {
  return date.toISOString().slice(0, 10);
}

const beforeDisplayValue = computed(() =>
  beforeInputValid.value && absoluteBefore.value
    ? toISODate(absoluteBefore.value)
    : beforeInputRaw.value,
);

const afterDisplayValue = computed(() =>
  afterInputValid.value && absoluteAfter.value
    ? toISODate(absoluteAfter.value)
    : afterInputRaw.value,
);

function onAbsoluteDateChange(which: "before" | "after", event: Event): void {
  const val = (event.target as HTMLInputElement).value;

  if (which === "before") {
    beforeInputRaw.value = val;
  } else {
    afterInputRaw.value = val;
  }

  const parsed = new Date(val);
  if (!isValidDate(parsed)) {
    if (which === "before") beforeInputValid.value = false;
    else afterInputValid.value = false;
    return;
  }

  const adjusted = new Date(parsed);
  if (which === "before") {
    adjusted.setUTCHours(23, 59, 59, 999);
    absoluteBefore.value = adjusted;
    beforeInputValid.value = true;
  } else {
    adjusted.setUTCHours(0, 0, 0, 0);
    absoluteAfter.value = adjusted;
    afterInputValid.value = true;
  }

  // Validate that end date is not before start date
  if (absoluteBefore.value && absoluteAfter.value) {
    if (absoluteBefore.value < absoluteAfter.value) {
      beforeInputValid.value = false;
      afterInputValid.value = false;
      return;
    }
    saveAbsoluteDates(absoluteBefore.value, absoluteAfter.value);
  }

  emitUpdate({
    before: absoluteBefore.value,
    after: absoluteAfter.value,
    relativeMode: false,
    allTime: false,
  });
}

// --- Mode switching ---

function switchToRelative(): void {
  relativeMode.value = true;
  saveMode("relative");
  applyRelativePreset(loadRelativeMillis());
}

function switchToAbsolute(): void {
  relativeMode.value = false;
  saveMode("absolute");
  const stored = loadAbsoluteDates();
  absoluteBefore.value = stored.before;
  absoluteAfter.value = stored.after;
  beforeInputRaw.value = toISODate(stored.before);
  afterInputRaw.value = toISODate(stored.after);
  beforeInputValid.value = true;
  afterInputValid.value = true;
  emitUpdate({
    before: stored.before,
    after: stored.after,
    relativeMode: false,
    allTime: false,
  });
}

function toggleMode(): void {
  if (relativeMode.value) {
    switchToAbsolute();
  } else {
    switchToRelative();
  }
}

// --- Init ---

onMounted(() => {
  if (loadMode() === "absolute") {
    switchToAbsolute();
    return;
  }

  if (props.before && props.after) {
    relativeMode.value = false;
    absoluteBefore.value = props.before;
    absoluteAfter.value = props.after;
    beforeInputRaw.value = toISODate(props.before);
    afterInputRaw.value = toISODate(props.after);
    beforeInputValid.value = true;
    afterInputValid.value = true;
    emitUpdate({
      before: props.before,
      after: props.after,
      relativeMode: false,
      allTime: false,
    });
    return;
  }

  relativeMode.value = true;
  applyRelativePreset(loadRelativeMillis());
});
</script>

<template>
  <div class="row">
    <div class="col">
      <div class="input-group mb-2">
        <!-- Absolute mode: start and end date inputs -->
        <template v-if="!relativeMode">
          <input
            type="date"
            id="after"
            class="form-control"
            :class="{ 'text-danger': !afterInputValid }"
            :value="afterDisplayValue"
            @change="onAbsoluteDateChange('after', $event)"
          />
          <span class="input-group-text">-</span>
          <input
            id="before"
            type="date"
            class="form-control"
            :class="{ 'text-danger': !beforeInputValid }"
            :value="beforeDisplayValue"
            @change="onAbsoluteDateChange('before', $event)"
          />
        </template>

        <!-- Relative mode: preset dropdown -->
        <template v-else>
          <select
            class="form-select"
            :value="selectedPreset"
            @change="
              applyRelativePreset(
                parseInt(($event.target as HTMLSelectElement).value),
              )
            "
          >
            <option
              v-for="option in PRESETS"
              :key="option.label"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </template>

        <!-- Mode toggle button -->
        <button
          v-if="toggleable"
          class="btn btn-sm btn-outline-secondary"
          @click="toggleMode"
          type="button"
          :title="
            relativeMode ? 'Switch to absolute mode' : 'Switch to relative mode'
          "
        >
          <i
            class="bi"
            :class="relativeMode ? 'bi-calendar-date' : 'bi-clock-history'"
          ></i>
        </button>
      </div>
    </div>
  </div>
</template>
