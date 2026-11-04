<script setup lang="ts">
defineProps<{ history: string[] }>();
</script>

<template>
  <div>
    <h6>History</h6>
    <div v-if="history.length === 0" class="text-body-secondary">
      No history
    </div>
    <ul v-else class="list-group list-group-flush small">
      <li
        v-for="(entry, i) in [...history].reverse()"
        :key="i"
        class="list-group-item px-0 font-monospace text-break"
      >
        {{ entry }}
      </li>
    </ul>
  </div>
</template>
