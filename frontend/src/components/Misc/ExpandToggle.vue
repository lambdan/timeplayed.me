<script setup lang="ts">
import "bootstrap-icons/font/bootstrap-icons.css";

// arrow button to show/hide the child games or platforms under a row, or a list
const expanded = defineModel<boolean>({ required: true });
withDefaults(defineProps<{ what?: string }>(), { what: "breakdown" });
</script>

<template>
  <button
    class="btn btn-sm btn-link p-0"
    type="button"
    :aria-expanded="expanded"
    :title="expanded ? `Hide ${what}` : `Show ${what}`"
    @click="expanded = !expanded"
  >
    <i :class="expanded ? 'bi bi-chevron-down' : 'bi bi-chevron-right'"></i>
  </button>
</template>
