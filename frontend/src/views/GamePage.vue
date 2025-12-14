<script setup lang="ts">
import { onMounted, ref } from "vue";
import RecentActivityCard from "../components/RecentActivityCard.vue";
import { useRoute } from "vue-router";
import GameInfoCard from "../components/GameInfoCard.vue";
import TopPlayersCard from "../components/Users/TopPlayersCard.vue";
import PlaytimeChart from "../components/Charts/PlaytimeChart.vue";
import type { GameWithStats } from "../api.models";

const route = useRoute();
const game = ref<GameWithStats>();

onMounted(async () => {
  const gameId = route.params.id as string;
  const gameRes = await fetch(`/api/game/${gameId}`);
  game.value = (await gameRes.json()) as GameWithStats;
});
</script>

<template>
  <GameInfoCard class="mb-4" v-if="game" :game="game.game" />
  <div class="card mt-4 p-0 mb-4">
    <PlaytimeChart v-if="game" :game="game.game" />
  </div>
  <div class="row">
    <div class="col mb-4">
      <TopPlayersCard v-if="game" :game="game.game" :limit="5" />
    </div>
    <div class="col mb-4">
      <RecentActivityCard v-if="game" :game="game.game" :limit="5" />
    </div>
  </div>
</template>
