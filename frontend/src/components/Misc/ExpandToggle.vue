<script setup lang="ts">
import "bootstrap-icons/font/bootstrap-icons.css";

// arrow button to show/hide the child games under a row
const expanded = defineModel<boolean>({ required: true });
</script>

<template>
  <button
    class="btn btn-sm btn-link p-0"
    type="button"
    :aria-expanded="expanded"
    :title="expanded ? 'Hide breakdown' : 'Show breakdown'"
    @click="expanded = !expanded"
  >
    <i :class="expanded ? 'bi bi-chevron-down' : 'bi bi-chevron-right'"></i>
  </button>
</template>
