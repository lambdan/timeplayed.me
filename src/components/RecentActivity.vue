<script lang="ts">
import { defineComponent } from "vue";
import type { API_Activities, Activity } from "../models/models";

export default defineComponent({
  name: "RecentActivity",

  props: {
    user: {
      type: String,
      required: false,
      default: null,
    },
  },

  data() {
    return {
      activities: [] as Activity[],
      loading: false,
      error: null as string | null,
    };
  },
  async mounted() {
    this.loading = true;
    try {
      let url = "/api/activities";
      if (this.user) {
        url += `?user=${this.user}`;
      }

      const res = await fetch(url);
      console.log(res);
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);

      const data: API_Activities = await res.json();
      this.activities = data.data;
    } catch (err: any) {
      this.error = err.message || "Unknown error";
    } finally {
      this.loading = false;
    }
  },
});
</script>

<template>
  <div v-if="loading">Loading...</div>
  <div v-else-if="error">Error: {{ error }}</div>
  <ul v-else>
    <li v-for="activity in activities" :key="activity.id">
      {{ activity.user.name }} played {{ activity.game.name }} on
      {{ activity.platform.name }} at
      {{ new Date(activity.timestamp).toISOString() }}.
    </li>
  </ul>
</template>
