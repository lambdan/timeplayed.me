<script setup lang="ts">
import { defineProps, ref } from "vue";
import "bootstrap-icons/font/bootstrap-icons.css";
import { formatDuration, timeAgo } from "../../utils";

const props = withDefaults(defineProps<{ secs: number }>(), {});
const showAbsolute = ref(false);

function toggle() {
  showAbsolute.value = !showAbsolute.value;
}
</script>

<template>
  <span
    :class="['badge', 'bg-timer']"
    @click="toggle()"
    style="cursor: pointer"
  >
    <i class="bi bi-stopwatch"></i>
    {{ showAbsolute ? `${props.secs} seconds` : formatDuration(props.secs) }}
  </span>
</template>
