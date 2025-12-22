<script setup lang="ts">
const props = withDefaults(defineProps<{ percent: number }>(), {});

function getVal() {
  return Math.min(100, Math.max(0, props.percent));
}
</script>

<template>
  <div
    class="progress"
    role="progressbar"
    :aria-valuenow="getVal()"
    aria-valuemin="0"
    aria-valuemax="100"
  >
    <div class="progress-bar" :style="'width:' + getVal() + '%'">
      {{ Math.round(getVal()) }} %
    </div>
  </div>
</template>
