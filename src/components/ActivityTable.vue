<script setup lang="ts">
import ActivityRow from "./ActivityRow.vue";
import type { Activity } from "../models/models";

defineProps<{ activities: Activity[] }>();
</script>

<template>
  <table class="table table-hover">
    <tbody>
      <ActivityRow
        v-for="activity in activities"
        :key="activity.id"
        :activity="activity"
      />
    </tbody>
  </table>
</template>
