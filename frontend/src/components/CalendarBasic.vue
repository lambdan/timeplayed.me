<script setup lang="ts">
import { onMounted, ref } from "vue";
import "bootstrap-icons/font/bootstrap-icons.css";
import { iso8601Date, timeAgo } from "../utils";

const props = withDefaults(
  defineProps<{
    date?: Date | number | null;
    absolute?: boolean;
    showIcon?: boolean;
  }>(),
  {
    absolute: false,
    showIcon: true,
  },
);

/* 
0: relative,
1: relative detailed, 
2: absolute UTC, 
3: absolute local, 
4: timestamp
*/
const MAX = 4;
const DEFAULT_ABSOLUTE = 2;
const mode = ref(0);
const showAbsolute = ref(props.absolute);
const textToDisplay = ref(text());
const hoverText = ref("-");

function toggle() {
  mode.value += 1;
  if (mode.value > MAX) {
    mode.value = 0;
  }
  textToDisplay.value = text();
}

function text(): string {
  function f() {
    if (!props.date) {
      return "-";
    }
    const reallyDate =
      typeof props.date === "number" ? new Date(props.date) : props.date;
    if (reallyDate.getTime() === 0) {
      return "-";
    }

    switch (mode.value) {
      case 0:
        return timeAgo(reallyDate);
      case 1:
        const delta = Date.now() - reallyDate.getTime();
        return Math.floor(delta / 1000) + " seconds ago";
      case 2:
        return iso8601Date(reallyDate, true);
      case 3:
        return reallyDate.toLocaleString();
      case 4:
        return reallyDate.getTime() + "";
      default:
        return "?";
    }
  }

  if (props.showIcon) {
    return " " + f();
  }
  return f();
}

onMounted(() => {
  if (showAbsolute.value) {
    mode.value = DEFAULT_ABSOLUTE;
  }
  textToDisplay.value = text();
  hoverText.value = props.date ? new Date(props.date).toUTCString() : "-";

  setInterval(() => {
    if (showAbsolute.value) return;
    textToDisplay.value = text();
  }, 1000);
});
</script>

<template>
  <span
    @click="toggle()"
    :title="hoverText"
    style="cursor: pointer; user-select: none"
  >
    <i class="bi bi-calendar" v-if="showIcon"></i>
    {{ textToDisplay }}
  </span>
</template>
