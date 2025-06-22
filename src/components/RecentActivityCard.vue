<script setup lang="ts">
import { onMounted, ref } from "vue";
import ActivityTable from "../components/ActivityTable.vue";
import type { Activity, API_Activities, User } from "../models/models";

const props = defineProps<{ user?: User; limit: number }>();

const activities = ref<Activity[]>([]);

async function fetchActivities(userId?: string, limit?: number) {
  if (props.user) {
    userId = props.user.id + "";
  }

  const params = [];
  if (userId) {
    params.push(`user=${userId}`);
  }
  if (limit) {
    params.push(`limit=${limit}`);
  }

  const res = await fetch(`/api/activities?${params.join("&")}`);
  const data: API_Activities = await res.json();

  activities.value = data.data.map((activity: any) => ({
    ...activity,
    createdAt: new Date(activity.timestamp),
  }));
}
onMounted(() => {
  let userId;
  if (props.user) {
    userId = props.user.id + "";
  }
  fetchActivities(userId, props.limit);
});
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
