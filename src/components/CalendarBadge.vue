<script setup lang="ts">
import type { Activity, Platform } from "../models/models";
import { defineProps } from "vue";
import "bootstrap-icons/font/bootstrap-icons.css";
import { timeAgo } from "../utils";

const props = withDefaults(
  defineProps<{ activity: Activity; absolute?: boolean }>(),
  {
    absolute: false,
  }
);

const ts = new Date(props.activity.timestamp);
</script>

<template>
  <span :class="['badge', 'bg-secondary']" :title="ts.toLocaleString()">
    <i class="bi bi-calendar"></i>

    {{ absolute ? ts.toLocaleString() : timeAgo(ts) }}
  </span>
</template>
