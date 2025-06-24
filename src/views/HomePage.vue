<script setup lang="ts">
import { onMounted, ref } from "vue";
import RecentActivityCard from "../components/RecentActivityCard.vue";
import type { Activity, GlobalStats } from "../models/models";

const globalStats = ref<GlobalStats>();
const loading = ref<boolean>(true);

onMounted(async () => {
  const res = await fetch("/api/stats");
  const data: GlobalStats = await res.json();
  globalStats.value = data;
  loading.value = false;
});
</script>

<template>
  <div class="card mb-4 p-0">
    <h1 class="card-header">Discord Playtime Tracker</h1>

    <div class="card-body text-start">
      <p class="lead">
        This is a thing that automatically tracks your playtime across games
        using Discord.
      </p>
      <p v-if="!loading">
        So far <b>{{ globalStats!.users }} users</b> have played
        <b>{{ globalStats!.games }} games</b> across
        <b>{{ globalStats!.platforms }} platforms</b> for a total of
        <b>{{ (globalStats!.total_playtime / 3600).toFixed(0) }} hours</b>.
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
