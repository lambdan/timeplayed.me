<script setup lang="ts">
import { onMounted, ref } from "vue";
import RecentActivityCard from "../components/RecentActivityCard.vue";
import type { Activity, API_Activities } from "../models/models";

const activities = ref<Activity[]>([]);

onMounted(async () => {
  const res = await fetch("/api/activities?limit=10");
  const data: API_Activities = await res.json();
  activities.value = data.data.map((activity) => ({
    ...activity,
    createdAt: new Date(activity.timestamp),
  }));
});
</script>

<template>
  <RecentActivityCard :limit="10" />
</template>
