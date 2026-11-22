<script setup lang="ts">
import { ref } from "vue";
import RecentActivityCard from "../components/RecentActivityCard.vue";
import TopGamesList from "../components/Games/TopGamesList.vue";
import TopPlatformsList from "../components/Platforms/TopPlatformsList.vue";
import DateRangerPicker from "../components/Misc/DateRangerPicker.vue";
import TopPlayersCard from "../components/Users/TopPlayersCard.vue";
import { getRecapYear } from "../utils";

const recapYear = ref(getRecapYear());
// date range for the top lists next to recent activity, set by their picker
const topAfter = ref<Date>();
const topBefore = ref<Date>();
// lists wait for the pickers first range, otherwise they'd fetch all time first
const topReady = ref(false);
</script>

<template>
  <div class="row g-4">
    <div class="col-12">
      <p class="lead">
        Track your playtime across all your games, on any platform.
      </p>
      <ul>
        <li>
          PC and <a href="/help#consoles">some consoles</a> can be tracked
          automatically using Discord
        </li>
        <li>
          Everything else can be tracked
          <a href="/manual-tracking">manually</a>
        </li>
        <li>
          You can also build your own tracking with the
          <a href="/help#api-section">API</a>
        </li>
      </ul>
      <p>
        To get started, join the Discord server. If you have Discord activity
        sharing enabled, your playtime will automatically start showing up here
        (<a href="/help#what-is-tracked">more info</a>).
      </p>
      <p>
        <a href="https://discord.gg/YyhX6KHE27" class="btn btn-primary">
          <i class="bi bi-discord"></i> Join the Discord server
        </a>
      </p>
      <marquee
        v-if="recapYear"
        behavior="scroll"
        direction="left"
        scrollamount="16"
      >
        <h2>
          {{ recapYear }} recap available! Look for a green button in your
          profile!
        </h2>
        <small
          >Yes this is a <code>&lt;marquee&gt;</code> in
          {{ new Date().getFullYear() }}. But you paid attention to it didn't
          you.</small
        >
      </marquee>
    </div>

    <!-- recent activity, and what's been played the most lately next to it -->
    <div class="col-lg-8">
      <RecentActivityCard :limit="25" />
    </div>
    <div class="col-lg-4">
      <!-- one card, the picker applies to everything in it -->
      <div class="card">
        <h2 class="card-header">Most played</h2>
        <div class="card-body d-flex flex-column gap-4">
          <DateRangerPicker
            storageKey="top"
            :relativeMillis="7 * 24 * 60 * 60 * 1000"
            @updated:both="
              ({ before, after }) => {
                topBefore = before;
                topAfter = after;
                topReady = true;
              }
            "
          />
          <template v-if="topReady">
            <TopGamesList :after="topAfter" :before="topBefore" :limit="10" />
            <TopPlatformsList
              :after="topAfter"
              :before="topBefore"
              :limit="10"
            />
            <TopPlayersCard
              :compact="true"
              :after="topAfter"
              :before="topBefore"
              :limit="10"
            />
          </template>
        </div>
      </div>
    </div>
  </div>
</template>
