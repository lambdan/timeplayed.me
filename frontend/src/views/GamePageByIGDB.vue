<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { TimeplayedAPI } from "../api.client";
import type { Game } from "../api.models";

const route = useRoute();
const game = ref<Game>();
const loading = ref(true);

onMounted(async () => {
  const igdbId = route.params.id as string;
  game.value = await TimeplayedAPI.getGameByIGDB(+igdbId);
  loading.value = false;
  if (game.value) {
    window.location.href = `/game/${game.value.id}`;
  }
});
</script>

<template>
  <p v-if="loading">Looking up game at IGDB...</p>
  <p v-if="game">Game found! Redirecting...</p>
  <p v-if="!game">Game not found</p>
</template>
