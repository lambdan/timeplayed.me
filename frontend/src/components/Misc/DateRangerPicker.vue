<script setup lang="ts">
import { defineProps, defineEmits, ref, onMounted } from "vue";


const localRelativeMode = ref(false);
const localRelativeDays = ref<number|undefined>();
const localBefore = ref<Date>(new Date());
const localAfter = ref<Date>(new Date(0));


const ONE_DAY = 24 * 60 * 60 * 1000;

const props = defineProps<{
    before?: Date;
    after?: Date;
    relativeDays?: number;
}>();

const emit = defineEmits<{
  (e: "update:before", value: Date): void;
  (e: "update:after", value: Date): void;
}>();

function setBefore(newBefore: Date) {
    localBefore.value = newBefore;
    emit("update:before", newBefore);
}

function setAfter(newAfter: Date) {
    localAfter.value = newAfter;
    emit("update:after", newAfter);
}

function nowMinus(days: number): number {
    return Date.now() - (days * ONE_DAY);
}

onMounted(() => {
    if (props.before && props.after) {
        localRelativeMode.value = false;
        setBefore(props.before);
        setAfter(props.after);
    } else if (props.relativeDays) {
        localRelativeDays.value = props.relativeDays;
        localRelativeMode.value = true;
        setBefore(new Date());
        setAfter(new Date(nowMinus(props.relativeDays!)));
    } else {
        // default to all time
        localRelativeMode.value = true;
        localRelativeDays.value = 0;
        setBefore(new Date());
        setAfter(new Date(0));
    }
});
</script>

<template>
  <div class="row">
    <div class="col" v-if="!localRelativeMode">
      <!-- absolute mode: one row for both dates -->
      <div class="input-group mb-2">
        <input
          id="after"
          type="datetime-isolocal"
          class="form-control"
          :value="localAfter.toISOString().slice(0, 10)"
          @change="
            setAfter(new Date(($event.target as HTMLInputElement)?.value))
          "
        />
        <span class="input-group-text">to</span>
        <input
          id="before"
          type="datetime-isolocal"
          class="form-control"
          :value="localBefore.toISOString().slice(0, 10)"
          @change="
            setBefore(new Date(($event.target as HTMLInputElement)?.value))
          "
        />
        <button
          class="btn btn-sm btn-outline-primary"
          @click="localRelativeMode = !localRelativeMode"
          type="button"
          title="Switch to relative mode"
        >
          <i
            class="bi"
            :class="localRelativeMode ? 'bi-calendar-date' : 'bi-clock-history'"
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
                setBefore(new Date());
              }
            "
            v-model="localRelativeDays"
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
            @click="localRelativeMode = !localRelativeMode"
            type="button"
            title="Switch to absolute mode"
          >
            <i
              class="bi"
              :class="localRelativeMode ? 'bi-calendar-date' : 'bi-clock-history'"
            ></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
