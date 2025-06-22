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
  <div class="card container mb-4 p-0">
    <h1 class="card-header">Discord Playtime Tracker</h1>

    <div class="card-body text-start">
      <p>
        This is a thing that automatically tracks your playtime across games
        using Discord.
        <br />
        So far, <b>XXX users</b> have played <b>XXX games</b> for a total of
        <b>XXX hours</b>.
      </p>
      <p>
        All you need to do is join the Discord server and you will be tracked:
        <br />
        <i class="bi bi-discord"></i> 
        <a href="https://discord.gg/YyhX6KHE27"
          >https://discord.gg/YyhX6KHE27</a
        >
        <br />
        <i
          >Please note that you need to be online and have activity sharing
          enabled, otherwise the bot can't see it.</i
        >
      </p>
      <p>
        You can also use the bot to track your playtime manually. DM the bot
        <code>!help</code> to see what's possible.
      </p>
      <hr />
      <p>Check the <a href="/news">news page</a> to see what's new!</p>
    </div>
  </div>

  <RecentActivityCard :limit="10" />
</template>
