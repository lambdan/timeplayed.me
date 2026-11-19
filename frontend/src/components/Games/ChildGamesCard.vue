<script setup lang="ts">
import type { GameWithStats } from "../../api.models";
import ChildGamesRows from "./ChildGamesRows.vue";

// the children of a game as a tree, each with the playtime of its own children included
defineProps<{ game: GameWithStats }>();
</script>

<template>
  <div class="card">
    <h2 class="card-header">Breakdown</h2>
    <div class="card-body">
      <table class="table table-sm table-hover align-middle mb-0">
        <thead>
          <tr>
            <th>Game</th>
            <th class="text-end">Playtime</th>
            <th class="text-end">Users</th>
            <th class="text-end d-none d-md-table-cell">Last played</th>
          </tr>
        </thead>
        <tbody>
          <ChildGamesRows :parent="game" :depth="0" />
        </tbody>
      </table>
    </div>
  </div>
</template>
