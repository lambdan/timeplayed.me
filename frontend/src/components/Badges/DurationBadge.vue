<script setup lang="ts">
import { formatDuration } from "../../utils";
import { heatBadgeStyle } from "../../utils.heat";

// a duration as hh:mm:ss, colored by length, same scale as the recap heatmap
defineProps<{
  seconds: number;
  /** makes it a link */
  href?: string;
}>();
</script>

<template>
  <component
    :is="href ? 'a' : 'span'"
    :href="href"
    class="badge fw-semibold text-decoration-none"
    :style="{ ...heatBadgeStyle(seconds), fontVariantNumeric: 'tabular-nums' }"
    >{{ formatDuration(seconds, true) }}</component
  >
</template>
