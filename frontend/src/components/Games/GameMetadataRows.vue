<script setup lang="ts">
import { ref } from "vue";
import type { Game } from "../../api.models";
import ExpandToggle from "../Misc/ExpandToggle.vue";
import { censor, useNsfw } from "../../composables/useNsfw";

// rows for the game's info table, below the stats
defineProps<{ game: Game }>();

const { isCensored } = useNsfw();
const showAliases = ref(false);
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
</template>
