<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import type { PlatformWithStats } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import PlatformBadge from "../components/Badges/PlatformBadge.vue";
import GameListCard from "../components/Games/GameListCard.vue";
import TopPlayersCard from "../components/Users/TopPlayersCard.vue";
import { formatDuration } from "../utils";

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
      <PlatformBadge :platform="platform.platform" class="p-2 mt-4" />

      <table class="table table-responsive table-hover p-2 mt-4">
        <tbody>
          <tr>
            <th>Games</th>
            <td>{{ platform.totals.game_count || "N/A" }}</td>
          </tr>
          <tr>
            <th>Users</th>
            <td>{{ platform.totals.user_count || "N/A" }}</td>
          </tr>
          <tr>
            <th>Total playtime</th>
            <td>
              {{ (platform.totals.playtime_secs / 3600).toFixed(0) }}
              hours
              <br />
              <span class="text-muted">
                {{
                  platform.percent
                    ? `(${(platform.percent * 100).toFixed(2)}% of all tracked playtime)`
                    : ""
                }}
              </span>
            </td>
          </tr>

          <tr>
            <th>Activity count</th>
            <td>
              {{ platform.totals.activity_count || "N/A" }}
            </td>
          </tr>
          <tr v-if="platform.oldest_activity">
            <th>First Played:</th>
            <td>
              <a :href="'/activity/' + platform.oldest_activity.id">
                {{
                  new Date(platform.oldest_activity.timestamp).toLocaleString()
                }}</a
              >
            </td>
          </tr>

          <tr v-if="platform.newest_activity">
            <th>Last Played:</th>
            <td>
              <a :href="'/activity/' + platform.newest_activity.id">
                {{
                  new Date(platform.newest_activity.timestamp).toLocaleString()
                }}</a
              >
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
        :platform="platform.platform"
        :showDateRange="true"
      ></GameListCard>

      <TopPlayersCard
        v-if="platform"
        :platform="platform.platform"
        :context="'platformPage'"
      ></TopPlayersCard>
    </div>
  </div>
</template>
