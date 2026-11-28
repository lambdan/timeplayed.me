<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import RecentActivityCard from "../components/RecentActivityCard.vue";
import { useRoute } from "vue-router";
import GameInfoCard from "../components/GameInfoCard.vue";
import TopPlayersCard from "../components/Users/TopPlayersCard.vue";
import TopPlatformsList from "../components/Platforms/TopPlatformsList.vue";
import GameMetadataCard from "../components/Games/GameMetadataCard.vue";
import YourStatsCard from "../components/Users/YourStatsCard.vue";
import ChildGamesCard from "../components/Games/ChildGamesCard.vue";
import DateRangerPicker from "../components/Misc/DateRangerPicker.vue";
import PlaytimeCharts from "../components/Charts/PlaytimeCharts.vue";
import type { GameWithStats } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import { usePageTitle } from "../composables/usePageTitle";

const route = useRoute();
const setTitle = usePageTitle();
const game = ref<GameWithStats>();
// stats including all child games, only fetched for games with children
const familyStats = ref<GameWithStats["stats"]>();
// the whole page includes the child games
const withChildren = computed(() => (game.value?.children_ids.length ?? 0) > 0);
// date range for the top lists next to recent activity, set by their picker
const topAfter = ref<Date>();
const topBefore = ref<Date>();
// lists wait for the pickers first range
const topReady = ref(false);

onMounted(async () => {
  const gameId = route.params.id as string;
  const loaded = await TimeplayedAPI.getGameStats(+gameId);
  // before showing the page, so the numbers don't change after a moment
  if (loaded.children_ids.length > 0) {
    const family = await TimeplayedAPI.getGameStats(+gameId, {
      include_children: true,
    });
    familyStats.value = family.stats;
  }
  game.value = loaded;

  if (game.value?.name) {
    let title = game.value.name;
    if (game.value.release_year) {
      title += ` (${game.value.release_year})`;
    }
    setTitle(`${title} playtime`);
  }
});
</script>

<template>
  <template v-if="game">
    <div class="row g-4">
      <div class="col-lg-8">
        <GameInfoCard class="h-100" :game="game" :familyStats="familyStats" />
      </div>
      <div class="col-lg-4 d-flex flex-column gap-4">
        <YourStatsCard :game="game" :includeChildren="withChildren" />
        <GameMetadataCard class="flex-grow-1" :game="game" />
      </div>

      <div v-if="game.children_ids.length > 0" class="col-12">
        <ChildGamesCard :game="game" />
      </div>

      <!-- recent activity, and who played it the most next to it -->
      <div class="col-lg-8">
        <RecentActivityCard
          :game="game"
          :includeChildren="withChildren"
          :limit="10"
        />
      </div>
      <div class="col-lg-4">
        <!-- one card, the picker applies to everything in it -->
        <div class="card">
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
                :includeChildren="withChildren"
                :compact="true"
                :after="topAfter"
                :before="topBefore"
                :limit="10"
              />
              <TopPlatformsList
                :game="game"
                :includeChildren="withChildren"
                :after="topAfter"
                :before="topBefore"
                :limit="10"
              />
            </template>
          </div>
        </div>
      </div>
      <div class="col-12">
        <PlaytimeCharts :game="game" :includeChildren="withChildren" />
      </div>
    </div>
  </template>
</template>
