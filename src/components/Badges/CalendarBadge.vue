<script setup lang="ts">
import type { Activity, Platform } from "../../models/models";
import { defineProps, ref } from "vue";
import "bootstrap-icons/font/bootstrap-icons.css";
import { timeAgo } from "../../utils";

const props = withDefaults(
  defineProps<{ date: Date | number; absolute?: boolean }>(),
  {
    absolute: false,
  }
);

const localDate = ref(props.date);

if (typeof props.date === "number") {
  // Convert timestamp to Date object
  localDate.value = new Date(props.date);
}

const ts = localDate.value;
const showAbsolute = ref(props.absolute);

function toggle() {
  showAbsolute.value = !showAbsolute.value;
}

function text() {
  if (!ts) {
    return "?";
  }
  if (showAbsolute.value) {
    return ts.toLocaleString();
  }
  return timeAgo(ts);
}
</script>

<template>
  <span
    :class="['badge', 'bg-calendar']"
    @click="toggle()"
    style="cursor: pointer"
  >
    <i class="bi bi-calendar"></i>
    {{ text() }}
  </span>
</template>
