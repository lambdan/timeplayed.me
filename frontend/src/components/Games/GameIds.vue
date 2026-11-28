<script setup lang="ts">
import type { Game } from "../../api.models";
import { useNsfw } from "../../composables/useNsfw";

// the game's own and external IDs, as a muted line
defineProps<{ game: Game }>();

// the external pages show the game, so they're left out for censored games
const { isCensored } = useNsfw();
</script>

<template>
  <div>
    ID {{ game.id }}
    <template v-if="game.igdb_id && !isCensored(game)">
      · IGDB
      <a v-if="game.igdb_url" :href="game.igdb_url" class="link-secondary">{{
        game.igdb_id
      }}</a>
      <template v-else>{{ game.igdb_id }}</template>
    </template>
    <template v-if="game.steam_id && !isCensored(game)">
      · Steam
      <a
        :href="'https://store.steampowered.com/app/' + game.steam_id"
        class="link-secondary"
        >{{ game.steam_id }}</a
      >
    </template>
  </div>
</template>
