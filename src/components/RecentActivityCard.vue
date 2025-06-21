<script setup lang="ts">
import ActivityTable from "../components/ActivityTable.vue";
import type { Activity } from "../models/models";

defineProps<{ activities: Activity[] }>();
</script>

<template>
  <div class="card">
    <h1 class="card-header">Recent activity</h1>
    <div class="card-body">
      <div class="row table-responsive">
        <ActivityTable :activities="activities" />
      </div>
    </div>
  </div>
</template>
