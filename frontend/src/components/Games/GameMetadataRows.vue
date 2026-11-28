<script setup lang="ts">
import { ref } from "vue";
import type { Game } from "../../api.models";
import ExpandToggle from "../Misc/ExpandToggle.vue";
import { censor, useNsfw } from "../../composables/useNsfw";

// rows for the game's info table, below the stats
defineProps<{ game: Game }>();

// the external pages show the game, so they're left out for censored games
const { isCensored } = useNsfw();
const showAliases = ref(false);
const showIds = ref(false);
</script>

<template>
  <tr v-if="game.aliases.length > 0">
    <th class="text-nowrap">Aliases</th>
    <td class="text-break">
      <ExpandToggle v-model="showAliases" what="aliases" />
      {{ game.aliases.length }}
      <template v-if="showAliases">
        <div v-for="alias in game.aliases" :key="alias">
          {{ isCensored(game) ? censor(alias) : alias }}
        </div>
      </template>
    </td>
  </tr>
  <tr>
    <th class="text-nowrap">IDs</th>
    <td>
      <ExpandToggle v-model="showIds" what="IDs" />
      <template v-if="showIds">
        <div>ID {{ game.id }}</div>
        <div v-if="game.igdb_id && !isCensored(game)">
          IGDB
          <a v-if="game.igdb_url" :href="game.igdb_url">{{ game.igdb_id }}</a>
          <template v-else>{{ game.igdb_id }}</template>
        </div>
        <div v-if="game.steam_id && !isCensored(game)">
          Steam
          <a :href="'https://store.steampowered.com/app/' + game.steam_id">{{
            game.steam_id
          }}</a>
        </div>
      </template>
    </td>
  </tr>
</template>
