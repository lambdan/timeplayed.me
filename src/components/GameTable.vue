<script setup lang="ts">
import type { Game } from "../models/models";
import GameRow from "./GameRow.vue";

const props = withDefaults(
  defineProps<{ games: Game[]; showExpand?: boolean }>(),
  {
    showExpand: false,
  }
);
</script>

<template>
  <table class="table table-hover">
    <tbody>
      <tr>
        <th></th>
        <!-- Cover -->

        <th>Name</th>
        <th>Last played</th>
        <th>Total playtime</th>
        <th></th>
      </tr>
      <GameRow
        v-for="game in games"
        :key="game.id"
        :game="game"
        :showExpand="showExpand"
      />
    </tbody>
  </table>
</template>
