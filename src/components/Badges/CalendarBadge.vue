<script setup lang="ts">
import { defineProps, onMounted, ref } from "vue";
import "bootstrap-icons/font/bootstrap-icons.css";
import { timeAgo } from "../../utils";

const props = withDefaults(
  defineProps<{ date: Date | number; absolute?: boolean }>(),
  {
    absolute: false,
  }
);

const showAbsolute = ref(props.absolute);
const textToDisplay = ref(text());

function toggle() {
  showAbsolute.value = !showAbsolute.value;
  textToDisplay.value = text(); // Update immediately on toggle
}

function text(): string {
  if (showAbsolute.value) {
    const reallyDate = typeof props.date === "number" ? new Date(props.date) : props.date;
    return reallyDate.toISOString();
  }
  return timeAgo(props.date);
}

onMounted(() => {
  textToDisplay.value = text();
  setInterval(() => {
    // Update the text every second, except when in absolute mode
    if (showAbsolute.value) return;
    textToDisplay.value = text();
  }, 1000);
});
</script>

<template>
  <span
    :class="['badge', 'bg-calendar']"
    @click="toggle()"
    style="cursor: pointer"
  >
    <i class="bi bi-calendar"></i>
    {{ textToDisplay }}
  </span>
</template>
