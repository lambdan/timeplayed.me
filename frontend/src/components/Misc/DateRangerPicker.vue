<script setup lang="ts">
// if you are reading this, i am sorry. i hate this fucking component too.
import { ref, onMounted } from "vue";

const ONE_HOUR = 60 * 60 * 1000;
const ONE_DAY = 24 * ONE_HOUR;
const ALL_TIME_MS = -1;

const _relativeMode = ref(false);
const _before = ref<Date | undefined>();
const _after = ref<Date | undefined>(); // timeplayed start date

const _beforeRaw = ref<any>(); // used to show error only,
const _afterRaw = ref<any>(); // not used for anything else

const _beforeValid = ref(false);
const _afterValid = ref(false);

const _relativeMillis = ref(ALL_TIME_MS);

const _toggleable = ref(true);

interface RelativeOption {
  label: string;
  milliseconds: number;
}

interface EmitData {
  before: Date | undefined;
  after: Date | undefined;
  allTime: boolean;
  relativeMode: boolean;
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
  { label: "All time", milliseconds: ALL_TIME_MS },
];

const props = defineProps<{
  before?: Date;
  after?: Date;
  relativeMillis?: number;
  toggleable?: boolean;
}>();

const emit = defineEmits<{
  (e: "updated:both", value: EmitData): void;
}>();

function getStoredDates() {
  // TODO: save/load to storage eventually
  const after = new Date(Date.now() - 10 * ONE_DAY);
  after.setUTCHours(0, 0, 0, 0);
  const before = new Date();
  before.setUTCHours(23, 59, 59, 999);
  return {
    after,
    before,
    relativeMillis: ALL_TIME_MS,
  };
}

function isValidDate(d: any): boolean {
  try {
    const date = new Date(d);
    if (isNaN(date.getTime())) {
      return false;
    }

    if (date.getUTCFullYear() < 2000 || date.getUTCFullYear() > 2100) {
      return false;
    }

    return true;
  } catch (e) {
    return false;
  }
}

let LAST_EMIT: EmitData | null = null;
let DEBOUNCE_ID = 0;
async function _emit(data: EmitData) {
  if (JSON.stringify(LAST_EMIT) === JSON.stringify(data)) {
    //console.log("_emit: no changes detected, not emitting");
    return;
  }

  // debounce
  DEBOUNCE_ID++;
  const id = DEBOUNCE_ID;
  await new Promise((r) => setTimeout(r, 400));
  if (id !== DEBOUNCE_ID) {
    return;
  }

  LAST_EMIT = data;
  emit("updated:both", data);
}

function maybeEmit(opts: { newBefore?: Date; newAfter?: Date }) {
  if (_relativeMode.value || opts.newBefore === undefined) {
    // before is always undefined in relative mode
    _before.value = undefined;
  } else if (isValidDate(opts.newBefore)) {
    _before.value = opts.newBefore;
  }
  _beforeValid.value = isValidDate(opts.newBefore);

  if (opts.newAfter === undefined) {
    _after.value = undefined;
  } else if (isValidDate(opts.newAfter)) {
    _after.value = opts.newAfter;
  }
  _afterValid.value = isValidDate(opts.newAfter);

  if (_before.value && _after.value) {
    if (_before.value < _after.value) {
      // invalid range
      _beforeValid.value = false;
      _afterValid.value = false;
      _beforeRaw.value = _before.value.toISOString().slice(0, 10);
      _afterRaw.value = _after.value.toISOString().slice(0, 10);
      return;
    }
  }

  _emit({
    before: _before.value,
    after: _after.value,
    relativeMode: _relativeMode.value,
    allTime: _after.value === undefined && _before.value === undefined,
  });
}

function iso8601(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function getDisplayed(which: "before" | "after"): string {
  if (which === "before") {
    if (_beforeValid.value === false) {
      return _beforeRaw.value;
    }
    return iso8601(_before.value!);
  }

  if (which === "after") {
    if (_afterValid.value === false) {
      return _afterRaw.value;
    }
    return iso8601(_after.value!);
  }

  throw new Error("youll never get here");
}

function switchToRelative() {
  const stored = getStoredDates().relativeMillis;
  _relativeMillis.value = stored;
  if (stored === ALL_TIME_MS) {
    maybeEmit({ newAfter: undefined, newBefore: undefined });
  } else {
    const after = new Date(Date.now() - stored);
    after.setUTCHours(0, 0, 0, 0);
    maybeEmit({ newAfter: after, newBefore: undefined });
  }
}

function switchToAbsolute() {
  const stored = getStoredDates();
  _before.value = stored.before;
  _after.value = stored.after;
  maybeEmit({ newBefore: stored.before, newAfter: stored.after });
}

function toggleMode() {
  _relativeMode.value = !_relativeMode.value;
  if (_relativeMode.value) {
    switchToRelative();
  } else {
    switchToAbsolute();
  }
}

function absoluteChanged(which: "before" | "after", newValue: any) {
  //console.log("absoluteChanged", which, newValue, typeof newValue);
  const val = (newValue as HTMLInputElement).value;
  //console.log("New date value:", val);

  if (which === "before") {
    _beforeRaw.value = val;
    //console.log("_beforeRaw", _beforeRaw.value);
  } else if (which === "after") {
    _afterRaw.value = val;
    //console.log("_afterRaw", _afterRaw.value);
  }

  let newDate: Date;
  try {
    newDate = new Date(val);
    console.log("Parsed date:", newDate);
  } catch (e) {
    //console.warn("absoluteChanged: invalid date format", newValue, e);
    if (which === "before") {
      _beforeValid.value = false;
    } else if (which === "after") {
      _afterValid.value = false;
    }
    return;
  }

  let adjusted = newDate;

  if (which === "before") {
    // set to end of day
    adjusted.setUTCHours(23, 59, 59, 999);
  } else if (which === "after") {
    // set to start of day
    adjusted.setUTCHours(0, 0, 0, 0);
  }

  if (which === "before") {
    maybeEmit({ newBefore: adjusted, newAfter: _after.value });
  } else if (which === "after") {
    maybeEmit({ newAfter: adjusted, newBefore: _before.value });
  }
}

function getDropdownValue(): string {
  for (const option of RELATIVE_VALUES) {
    const x = option.milliseconds.toString();
    const y = _relativeMillis.value.toString();
    if (x === y) {
      return x;
    }
  }
  console.warn(
    "getDropdownValue: no matching value for",
    _relativeMillis.value,
  );
  return "-1";
}

function parseDropdown(n: any) {
  if (typeof n === "string") {
    n = parseInt(n);
  }
  if (typeof n !== "number") {
    return;
  }
  if (n === ALL_TIME_MS) {
    // all time
    _relativeMillis.value = ALL_TIME_MS;
    maybeEmit({ newAfter: undefined, newBefore: undefined });
    return;
  } else {
    const after = new Date(Date.now() - n);
    after.setUTCHours(0, 0, 0, 0);
    maybeEmit({ newAfter: after, newBefore: undefined });
  }
}

onMounted(() => {
  _toggleable.value = props.toggleable !== false;
  if (props.before && props.after) {
    _relativeMode.value = false;
    maybeEmit({ newBefore: props.before, newAfter: props.after });
  } else if (props.relativeMillis) {
    _relativeMode.value = true;
    maybeEmit({ newAfter: new Date(Date.now() - props.relativeMillis) });
  } else {
    // default to all time
    _relativeMode.value = true;
    maybeEmit({});
  }
});
</script>

<template>
  <div class="row">
    <div class="col" v-if="!_relativeMode">
      <!-- absolute mode: one row for both dates -->
      <div class="input-group mb-2">
        <input
          type="date"
          id="after"
          class="form-control"
          :class="{ 'text-danger': !_afterValid }"
          :value="getDisplayed('after')"
          @change="absoluteChanged('after', $event.target as HTMLInputElement)"
        />
        <span class="input-group-text">-</span>
        <input
          id="before"
          type="date"
          class="form-control"
          :class="_beforeValid ? '' : 'text-danger'"
          :value="getDisplayed('before')"
          @change="absoluteChanged('before', $event.target as HTMLInputElement)"
        />
        <!-- Switch mode button -->
        <button
          v-if="_toggleable"
          class="btn btn-sm btn-outline-secondary"
          @click="toggleMode()"
          type="button"
          title="Switch to relative mode"
        >
          <i
            class="bi"
            :class="_relativeMode ? 'bi-calendar-date' : 'bi-clock-history'"
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
            :value="getDropdownValue()"
            @change="
              (e) => {
                const val = (e.target as HTMLSelectElement).value;
                parseDropdown(val);
              }
            "
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
            v-if="_toggleable"
            class="btn btn-sm btn-outline-secondary"
            @click="toggleMode()"
            type="button"
            title="Switch to absolute mode"
          >
            <i
              class="bi"
              :class="_relativeMode ? 'bi-calendar-date' : 'bi-clock-history'"
            ></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
