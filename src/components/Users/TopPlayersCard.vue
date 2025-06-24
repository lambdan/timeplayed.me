<script setup lang="ts">
import { ref } from "vue";
import type { Game, User } from "../../models/models";
import UserTable from "./UserTable.vue";

const props = withDefaults(
  defineProps<{
    game: Game;
  }>(),
  {}
);
</script>

<template>
  <div class="card p-0">
    <h1 class="card-header">Top players</h1>
    <div class="card-body">
      <UserTable :game="game" :sort="'playtime'" :order="'desc'" />
    </div>
  </div>
</template>
