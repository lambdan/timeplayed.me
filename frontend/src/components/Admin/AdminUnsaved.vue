<script setup lang="ts">
/** shown next to a save button, lists what hasn't been saved yet */
defineProps<{ labels: string[] }>();
</script>

<template>
  <span v-if="labels.length" class="text-warning-emphasis small">
    <i class="bi bi-exclamation-triangle-fill"></i>
    Unsaved: {{ labels.join(", ") }}
  </span>
</template>
