<script setup lang="ts">
import "bootstrap-icons/font/bootstrap-icons.css";
import { onMounted, ref } from "vue";
import { TimeplayedAPI } from "../../api.client";

const props = defineProps<{
  gameId: number;
}>();

const text = ref(props.gameId + "");
const fetched = ref(false);

async function fetchOrGetCachedGame(gameId: number): Promise<string> {
  const storageKey = `game_name_${gameId}`;
  const cachedName = sessionStorage.getItem(storageKey);
  if (cachedName) {
    return cachedName;
  }
  const game = await TimeplayedAPI.getGame(gameId);
  const gameName = game.game.name;
  sessionStorage.setItem(storageKey, gameName);
  return gameName;
}

onMounted(async () => {
  text.value = await fetchOrGetCachedGame(props.gameId);
  fetched.value = true;
});
</script>

<template>
  <span class="badge bg-secondary me-1 mb-1">
    <a :href="'/game/' + gameId" class="text-white text-decoration-none">
      {{ text }}
    </a>
    <span
      v-if="!fetched"
      class="spinner-border spinner-border-sm ms-2"
      role="status"
      aria-hidden="true"
    ></span>
  </span>
</template>
