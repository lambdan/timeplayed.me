<script setup lang="ts">
/** shown next to a save button, lists what hasn't been saved yet */
defineProps<{ labels: string[] }>();
const emit = defineEmits<{ revert: [] }>();
</script>

<template>
  <template v-if="labels.length">
    <button class="btn btn-outline-secondary btn-sm" @click="emit('revert')">
      Revert
    </button>
    <span class="text-warning-emphasis small">
      <i class="bi bi-exclamation-triangle-fill"></i>
      Unsaved: {{ labels.join(", ") }}
    </span>
  </template>
</template>
