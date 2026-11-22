<script setup lang="ts">
import type { AdminHistory } from "../../admin.client";
import { formatDate } from "../../utils";

defineProps<{ history: AdminHistory[] }>();
</script>

<template>
  <div>
    <h6>History</h6>
    <div v-if="history.length === 0" class="text-body-secondary">
      No history
    </div>
    <div v-else class="table-responsive">
      <table class="table table-sm small">
        <thead>
          <tr>
            <th>Time</th>
            <th>By</th>
            <th>Message</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(entry, i) in [...history].reverse()" :key="i">
            <td class="text-nowrap">{{ formatDate(entry.timestamp) }}</td>
            <td class="text-nowrap">{{ entry.actor_name }}</td>
            <td class="font-monospace text-break">{{ entry.message }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
