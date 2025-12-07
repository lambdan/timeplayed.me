<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { GameWithStats } from "../../models/models";
import GameCover from "./GameCover.vue";
import CalendarBadge from "../Badges/CalendarBadge.vue";
import DurationBadge from "../Badges/DurationBadge.vue";

const props = withDefaults(defineProps<{ game: GameWithStats }>(), {});


onMounted(async () => {});
</script>

<template>
  <div class="row align-items-center mb-2" :title="'Game ID ' + game.game.id">
    <div class="col col-lg-1">
      <GameCover :gameId="game.game.id" :thumb="true" :maxHeight="100" />
    </div>

    <div class="col text-start">
      <a
        class="text-decoration-none link-primary"
        :href="`/game/${game.game.id}`"
        >{{ game.game.name }}</a
      >
      <br />
      <CalendarBadge :date="game.last_played" title="Last played" />
       
      <DurationBadge :secs="game.total_playtime" title="Total playtime" />
    </div>
  </div>
  <hr />
</template>
