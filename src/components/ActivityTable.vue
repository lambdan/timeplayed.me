<script setup lang="ts">
import ActivityRow from "./ActivityRow.vue";
import type { Activity } from "../models/models";

const props = withDefaults(
  defineProps<{ activities: Activity[]; showExpand?: boolean }>(),
  {
    showExpand: false,
  }
);
</script>

<template>
  <table class="table table-hover">
    <tbody>
      <ActivityRow
        v-for="activity in activities"
        :key="activity.id"
        :activity="activity"
        :showExpand="showExpand"
      />
    </tbody>
  </table>
</template>
