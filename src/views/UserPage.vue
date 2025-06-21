<script setup lang="ts">
import { onMounted, ref } from "vue";
import UserInfoCard from "../components/UserInfoCard.vue";
import RecentActivityCard from "../components/RecentActivityCard.vue";
import {
  type User,
  type Activity,
  type API_Activities,
} from "../models/models";
import { useRoute } from "vue-router";

const route = useRoute();
const activities = ref<Activity[]>([]);
const user = ref<User>();

onMounted(async () => {
  const userId = route.params.id as string;
  const res = await fetch(`/api/activities?user=${userId}`);
  const data: API_Activities = await res.json();
  activities.value = data.data.map((activity) => ({
    ...activity,
    createdAt: new Date(activity.timestamp),
  }));
  const userRes = await fetch(`/api/users/${userId}`);
  user.value = await userRes.json();
});
</script>

<template>
  <UserInfoCard v-if="user" :user="user" />
  <RecentActivityCard :activities="activities" />
</template>
