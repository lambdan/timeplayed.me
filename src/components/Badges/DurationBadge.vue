<script setup lang="ts">
import type { Activity, Platform } from "../../models/models";
import { defineProps } from "vue";
import "bootstrap-icons/font/bootstrap-icons.css";
import { formatDuration, timeAgo } from "../../utils";

const props = withDefaults(defineProps<{ activity: Activity }>(), {});
const secs = props.activity.seconds || 0;
</script>

<template>
  <span
    :class="['badge', 'bg-secondary']"
    :title="props.activity.seconds + ' seconds'"
  >
    <i class="bi bi-stopwatch"></i>
    {{ formatDuration(secs) }}
  </span>
</template>
