<script setup lang="ts">
import type { Activity, Platform } from "../models/models";
import { defineProps } from "vue";
import "bootstrap-icons/font/bootstrap-icons.css";
import { formatDuration } from "../utils";

const props = withDefaults(
  defineProps<{ activity: Activity; plain?: boolean }>(),
  {
    plain: false,
  }
);
const secs = props.activity.seconds;
</script>

<template>
  <span v-if="props.plain">
    {{ formatDuration(secs) }}
  </span>

  <span v-else :class="['badge', 'bg-secondary']">
    <i class="bi bi-stopwatch"></i>
    {{ formatDuration(secs) }}
  </span>
</template>
