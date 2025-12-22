<script setup lang="ts">
import { onMounted, ref } from "vue";
import RecentActivityCard from "../components/RecentActivityCard.vue";
import PlaytimeChart from "../components/Charts/PlaytimeChart.vue";
import TopPlayersCard from "../components/Users/TopPlayersCard.vue";
import type { Totals } from "../api.models";

const globalStats = ref<Totals>();
const fetching = ref(false);

onMounted(async () => {
  fetching.value = true;
  const res = await fetch("/api/totals");
  const data: Totals = await res.json();
  fetching.value = false;
  globalStats.value = data;
  // keep refreshing
  setInterval(async () => {
    fetching.value = true;
    const res = await fetch("/api/totals");
    const data: Totals = await res.json();
    globalStats.value = data;
    await new Promise((r) => setTimeout(r, 500));
    fetching.value = false;
  }, 5000);
});
</script>

<template>
  <div class="row">
    <div class="col card p-0 mt-4">
      <h1 class="card-header">Discord Playtime Tracker</h1>

      <div class="card-body text-start">
        <p class="lead">
          This is a thing that automatically tracks your playtime across games
          using Discord.
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
              {{ new Date().getFullYear() }}. But you paid attention to it
              didn't you.</small
            >
          </marquee>
        </div>
      </div>
    </div>
    <div class="col-lg-4 card p-0 mt-4">
      <h1 class="card-header">
        Totals

        <span
          v-if="fetching"
          class="spinner-border spinner-border-sm float-end mt-3"
          role="status"
          aria-hidden="true"
        ></span>
      </h1>
      <div class="card-body">
        <ul class="list-group list-group-flush" v-if="globalStats">
          <li class="list-group-item py-1 px-2">
            <span class="fw-bold float-start" title="ah ah he said it"
              >Time played</span
            >
            <span class="float-end"
              >{{ (globalStats.playtime_secs / 3600).toFixed(0) }} hours<br />
            </span>
          </li>

          <li class="list-group-item py-1 px-2">
            <span class="fw-bold float-start">Activity count</span>
            <span class="float-end">{{ globalStats.activity_count }}</span>
          </li>

          <li class="list-group-item py-1 px-2">
            <span class="fw-bold float-start">Users</span>
            <span class="float-end">{{ globalStats.user_count }}</span>
          </li>

          <li class="list-group-item py-1 px-2">
            <span class="fw-bold float-start">Games</span>
            <span class="float-end">{{ globalStats.game_count }}</span>
          </li>

          <li class="list-group-item py-1 px-2">
            <span class="fw-bold float-start">Platforms</span>
            <span class="float-end">{{ globalStats.platform_count }}</span>
          </li>
        </ul>
      </div>
    </div>
  </div>

  <div class="row mt-4">
    <PlaytimeChart class="card p-0" />
  </div>

  <div class="row mb-4">
    <TopPlayersCard class="col-lg p-0 mt-4" context="frontPage" />
    <RecentActivityCard :limit="10" class="col-lg p-0 mt-4" />
  </div>
</template>
