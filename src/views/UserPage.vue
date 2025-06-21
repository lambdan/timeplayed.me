<script setup lang="ts">
import { onMounted, ref } from "vue";
import RecentActivityCard from "../components/RecentActivityCard.vue";
import type { Activity, API_Activities } from "../models/models";
import { useRoute } from "vue-router";

const route = useRoute();
const activities = ref<Activity[]>([]);

onMounted(async () => {
  const userId = route.params.id as string;
  const res = await fetch(`/api/activities?user=${userId}`);
  const data: API_Activities = await res.json();
  activities.value = data.data.map((activity) => ({
    ...activity,
    createdAt: new Date(activity.timestamp),
  }));
});
</script>

<template>
  <RecentActivityCard :activities="activities" />
</template>
