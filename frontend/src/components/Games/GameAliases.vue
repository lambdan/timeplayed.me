<script setup lang="ts">
import { ref } from "vue";
import type { Game } from "../../api.models";
import ExpandToggle from "../Misc/ExpandToggle.vue";
import { censor, useNsfw } from "../../composables/useNsfw";

// the game's aliases, collapsed to a count
defineProps<{ game: Game }>();

const { isCensored } = useNsfw();
const showAliases = ref(false);
</script>

<template>
  <div v-if="game.aliases.length > 0" class="small text-muted">
    <ExpandToggle v-model="showAliases" what="aliases" />
    {{ game.aliases.length }}
    {{ game.aliases.length === 1 ? "alias" : "aliases" }}
    <div v-if="showAliases" class="text-break">
      <div v-for="alias in game.aliases" :key="alias">
        {{ isCensored(game) ? censor(alias) : alias }}
      </div>
    </div>
  </div>
</template>
