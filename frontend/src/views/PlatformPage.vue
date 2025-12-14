<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import type { PlatformWithStats } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import PlatformBadge from "../components/Badges/PlatformBadge.vue";
import GameListCard from "../components/Games/GameListCard.vue";
import TopPlayersCard from "../components/Users/TopPlayersCard.vue";

const route = useRoute();
const platform = ref<PlatformWithStats>();
const loading = ref(false);

async function fetchPlatform() {
  const platformId = parseInt(route.params.id as string);
  loading.value = true;
  platform.value = await TimeplayedAPI.getPlatform(platformId);
  loading.value = false;
}

onMounted(async () => {
  await fetchPlatform();
});
</script>

<template>
  <p v-if="loading">Loading...</p>

  <div v-if="!loading && platform" class="card p-0">
    <h1 class="card-header">
      {{ platform.platform.name || platform.platform.abbreviation }}
    </h1>
    <div class="card-body">
      <PlatformBadge :platform="platform.platform" class="mb-3" />
      <p><strong>Games:</strong> {{ platform.totals.game_count }}</p>
      <p><strong>Users:</strong> {{ platform.totals.user_count }}</p>
      <p>
        <strong>Total Playtime:</strong>
        {{ (platform.totals.playtime_secs / 3600).toFixed(0) }} hours
        {{
          platform.percent
            ? `(${(platform.percent * 100).toFixed(2)}% of all tracked playtime)`
            : ""
        }}
      </p>
      <p>
        <strong>Last Played:</strong>
        {{
          platform.newest_activity
            ? new Date(platform.newest_activity.timestamp).toLocaleString()
            : "Never"
        }}
      </p>
      <p>
        <strong>First Played:</strong>
        {{
          platform.oldest_activity
            ? new Date(platform.oldest_activity.timestamp).toLocaleString()
            : "Never"
        }}
      </p>

      <hr />

      <GameListCard
        v-if="platform"
        class="mb-4"
        :limit="10"
        :order="'desc'"
        :sort="'playtime'"
        :platform="platform.platform"
      ></GameListCard>

      <TopPlayersCard
        v-if="platform"
        :platform="platform.platform"
        :startingRelativeDays="30"
      ></TopPlayersCard>
    </div>
  </div>
</template>
