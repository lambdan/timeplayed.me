<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  label: string;
  value: string;
  sub?: string;
  /** % change vs previous year */
  change?: number;
  previousYear?: number;
  /** smaller value and padding, for the game and platform info cards */
  small?: boolean;
  /** colors instead of the default tile background, like a platform's */
  background?: string;
  color?: string;
}>();

const changeText = computed(() => {
  if (props.change === undefined) return undefined;
  const sign = props.change >= 0 ? "+" : "−";
  return `${sign}${Math.abs(props.change).toFixed(0)}% vs ${props.previousYear}`;
});
</script>

<template>
  <div
    class="rounded h-100"
    :class="[
      small ? 'p-2' : 'p-3',
      background ? '' : 'border bg-body-tertiary',
    ]"
    :style="background ? { backgroundColor: background, color } : undefined"
  >
    <div
      class="small text-uppercase fw-semibold"
      :class="background ? 'opacity-75' : 'text-body-secondary'"
    >
      {{ label }}
    </div>
    <div class="fw-bold lh-sm" :class="small ? 'fs-4' : 'fs-2'">
      {{ value }}
    </div>
    <!-- slot for subs with links in them -->
    <div
      v-if="sub || $slots.default"
      class="small"
      :class="background ? 'opacity-75' : 'text-body-secondary'"
    >
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
