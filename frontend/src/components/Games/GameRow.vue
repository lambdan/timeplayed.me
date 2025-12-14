<script setup lang="ts">
import { onMounted, ref } from "vue";
import GameCover from "./GameCover.vue";
import CalendarBadge from "../Badges/CalendarBadge.vue";
import DurationBadge from "../Badges/DurationBadge.vue";
import type { GameWithStats } from "../../api.models";

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
      <CalendarBadge
        v-if="game.newest_activity"
        :date="game.newest_activity.timestamp"
        title="Last played"
      />
       
      <DurationBadge :secs="game.totals.playtime_secs" title="Total playtime" />
    </div>
  </div>
  <hr />
</template>
