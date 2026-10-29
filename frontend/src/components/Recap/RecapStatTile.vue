<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  label: string;
  value: string;
  sub?: string;
  /** % change vs previous year */
  change?: number;
  previousYear?: number;
}>();

const changeText = computed(() => {
  if (props.change === undefined) return undefined;
  const sign = props.change >= 0 ? "+" : "−";
  return `${sign}${Math.abs(props.change).toFixed(0)}% vs ${props.previousYear}`;
});
</script>

<template>
  <div class="border rounded bg-body-tertiary p-3 h-100">
    <div class="small text-uppercase fw-semibold text-body-secondary">
      {{ label }}
    </div>
    <div class="fs-2 fw-bold lh-sm">{{ value }}</div>
    <!-- slot for subs with links in them -->
    <div v-if="sub || $slots.default" class="small text-body-secondary">
      <slot>{{ sub }}</slot>
    </div>
    <div
      v-if="changeText"
      class="small"
      :class="change! >= 0 ? 'text-success' : 'text-danger'"
    >
      {{ changeText }}
    </div>
  </div>
</template>
