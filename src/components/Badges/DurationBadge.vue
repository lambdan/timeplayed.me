<script setup lang="ts">
import { defineProps } from "vue";
import "bootstrap-icons/font/bootstrap-icons.css";
import { formatDuration, timeAgo } from "../../utils";

const props = withDefaults(defineProps<{ secs: number }>(), {});
</script>

<template>
  <span :class="['badge', 'bg-secondary']" :title="props.secs + ' seconds'">
    <i class="bi bi-stopwatch"></i>
    {{ formatDuration(props.secs) }}
  </span>
</template>
