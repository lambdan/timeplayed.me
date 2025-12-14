<script setup lang="ts">
import { onMounted, ref } from "vue";
import RecentActivityCard from "../components/RecentActivityCard.vue";
import PlaytimeChart from "../components/Charts/PlaytimeChart.vue";
import TopPlayersCard from "../components/Users/TopPlayersCard.vue";
import type { Totals } from "../api.models";

const globalStats = ref<Totals>();
const loading = ref<boolean>(true);

onMounted(async () => {
  const res = await fetch("/api/totals");
  const data: Totals = await res.json();
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
        So far <b>{{ globalStats!.user_count }} users</b> have played
        <b>{{ globalStats!.game_count }} games</b> across
        <b>{{ globalStats!.platform_count }} platforms</b> for a total of
        <b>{{ (globalStats!.playtime_secs / 3600).toFixed(0) }} hours</b>.
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
      <!-- <p>Check the <a href="/news">news page</a> to see what's new!</p> -->
      <div v-if="new Date().getMonth() === 11 || new Date().getMonth() === 0">
        <!-- december or january -->
        <marquee behavior="scroll" direction="left" scrollamount="16">
          <!-- if december, show current year. if january, show previous year -->
          <h2>
            {{
              new Date().getMonth() === 11
                ? new Date().getFullYear()
                : new Date().getFullYear() - 1
            }}
            Year Recap now available! Look for a green button in your profile!
          </h2>
          <small
            >Yes this is a <code>&lt;marquee&gt;</code> in the year
            {{ new Date().getFullYear() }}. But you paid attention to it didn't
            you.</small
          >
        </marquee>
      </div>
    </div>
  </div>

  <div class="card mt-4 p-0 mb-4">
    <PlaytimeChart />
  </div>
  <div class="row">
    <div class="col-lg-4 mb-4">
      <TopPlayersCard :startingRelativeDays="7" />
    </div>
    <div class="col mb-4">
      <RecentActivityCard :limit="10" />
    </div>
    <PlatformListCard
      :showExpand="false"
      :limit="25"
      :order="'desc'"
      :sort="'playtime'"
      :showSortButtons="false"
    ></PlatformListCard>
  </div>
</template>
