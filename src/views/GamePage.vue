<script setup lang="ts">
import { onMounted, ref } from "vue";
import RecentActivityCard from "../components/RecentActivityCard.vue";
import { type Game, type GameWithStats } from "../models/models";
import { useRoute } from "vue-router";
import GameInfoCard from "../components/GameInfoCard.vue";

const route = useRoute();
const game = ref<GameWithStats>();

onMounted(async () => {
  const gameId = route.params.id as string;
  const gameRes = await fetch(`/api/games/${gameId}`);
  game.value = (await gameRes.json()) as GameWithStats;
});
</script>

<template>
  <GameInfoCard class="mb-4" v-if="game" :game="game.game" />
  <RecentActivityCard v-if="game" :game="game.game" :limit="5" class="mb-4" />
</template>
