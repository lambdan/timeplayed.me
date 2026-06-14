<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import type { PlatformWithStats } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import PlatformBadge from "../components/Badges/PlatformBadge.vue";
import GameListCard from "../components/Games/GameListCard.vue";
import TopPlayersCard from "../components/Users/TopPlayersCard.vue";
import { formatDuration, iso8601Date } from "../utils";

const route = useRoute();
const platform = ref<PlatformWithStats>();
const loading = ref(false);

async function fetchPlatform() {
  const platformId = parseInt(route.params.id as string);
  loading.value = true;
  platform.value = await TimeplayedAPI.getPlatformStats(platformId);
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
      {{ platform.name || platform.abbreviation }}
    </h1>
    <div class="card-body">
      <PlatformBadge :platform="platform" class="p-2 mt-4" />

      <table class="table table-responsive table-hover p-2 mt-4">
        <tbody>
          <tr>
            <th>Games</th>
            <td>{{ platform.stats.game_count || "N/A" }}</td>
          </tr>
          <tr>
            <th>Users</th>
            <td>{{ platform.stats.user_count || "N/A" }}</td>
          </tr>
          <tr>
            <th>Total playtime</th>
            <td>
              {{ formatDuration(platform.stats.seconds) }}
            </td>
          </tr>

          <tr>
            <th>Activity count</th>
            <td>
              {{ platform.stats.activity_count || "N/A" }}
            </td>
          </tr>
          <tr v-if="platform.stats.first_activity">
            <th>First Played:</th>
            <td>
              {{ iso8601Date(new Date(platform.stats.first_activity), true) }}
            </td>
          </tr>

          <tr v-if="platform.stats.last_activity">
            <th>Last Played:</th>
            <td>
              {{ iso8601Date(new Date(platform.stats.last_activity), true) }}
            </td>
          </tr>
        </tbody>
      </table>

      <GameListCard
        v-if="platform"
        class="mb-4"
        :limit="10"
        :order="'desc'"
        :sort="'playtime'"
        :platform="platform"
        :showDateRange="true"
      ></GameListCard>

      <TopPlayersCard
        v-if="platform"
        :platform="platform"
        :context="'platformPage'"
      ></TopPlayersCard>
    </div>
  </div>
</template>
