<script setup lang="ts">
import { onMounted, ref } from "vue";
import RecentActivityCard from "../components/RecentActivityCard.vue";
import { useRoute } from "vue-router";
import GameInfoCard from "../components/GameInfoCard.vue";
import TopPlayersCard from "../components/Users/TopPlayersCard.vue";
import TopPlatformsList from "../components/Platforms/TopPlatformsList.vue";
import GameMetadataCard from "../components/Games/GameMetadataCard.vue";
import DateRangerPicker from "../components/Misc/DateRangerPicker.vue";
import PlaytimeChart from "../components/Charts/PlaytimeChart.vue";
import type { GameWithStats } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import { updateDocumentTitle } from "../utils";

const route = useRoute();
const game = ref<GameWithStats>();
// date range for the top lists next to recent activity, set by their picker
const topAfter = ref<Date>();
const topBefore = ref<Date>();
// lists wait for the pickers first range
const topReady = ref(false);

onMounted(async () => {
  const gameId = route.params.id as string;
  game.value = await TimeplayedAPI.getGameStats(+gameId);

  if (game.value?.name) {
    let title = game.value.name;
    if (game.value.release_year) {
      title += ` (${game.value.release_year})`;
    }
    updateDocumentTitle(title);
  }
});
</script>

<template>
  <template v-if="game">
    <div class="row">
      <div class="col-lg-8 p-0 pe-lg-4 mt-4">
        <GameInfoCard class="h-100" :game="game" />
      </div>
      <div class="col-lg-4 p-0 mt-4">
        <GameMetadataCard class="h-100" :game="game" />
      </div>
    </div>

    <!-- recent activity, and who played it the most next to it -->
    <div class="row mt-4">
      <div class="col-lg-8 p-0 pe-lg-4">
        <RecentActivityCard :game="game" :limit="10" />
      </div>
      <div class="col-lg-4 p-0 mt-4 mt-lg-0">
        <!-- one card, the picker applies to everything in it -->
        <div class="card p-0">
          <h2 class="card-header">Top lists</h2>
          <div class="card-body d-flex flex-column gap-4">
            <DateRangerPicker
              storageKey="top"
              :relativeMillis="-1"
              @updated:both="
                ({ before, after }) => {
                  topBefore = before;
                  topAfter = after;
                  topReady = true;
                }
              "
            />
            <template v-if="topReady">
              <TopPlayersCard
                :game="game"
                :compact="true"
                :after="topAfter"
                :before="topBefore"
                :limit="10"
              />
              <TopPlatformsList
                :game="game"
                :after="topAfter"
                :before="topBefore"
                :limit="10"
              />
            </template>
          </div>
        </div>
      </div>
    </div>

    <div class="row mt-4 mb-4">
      <PlaytimeChart class="card p-0" :game="game" />
    </div>
  </template>
</template>
