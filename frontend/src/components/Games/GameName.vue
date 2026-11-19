<script setup lang="ts">
import { useNsfw } from "../../composables/useNsfw";

defineProps<{ game: { name: string; nsfw?: boolean } }>();

const { isCensored, gameName } = useNsfw();
</script>

<template>
  <span v-if="isCensored(game)" class="text-danger" title="NSFW">{{
    gameName(game)
  }}</span>
  <template v-else>{{ game.name }}</template>
</template>
