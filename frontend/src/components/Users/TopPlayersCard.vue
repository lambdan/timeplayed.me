<script setup lang="ts">
import { ref } from "vue";
import type { Game, User } from "../../models/models";
import UserTable from "./UserTable.vue";

const props = withDefaults(
  defineProps<{
    game?: Game;
  }>(),
  {
    game: undefined,
  }
);
</script>

<template>
  <div class="card p-0">
    <h2 class="card-header">Top players</h2>
    <div class="card-body">
      <UserTable :game="game" :sort="'playtime'" :order="'desc'" :show-date-range="true" />
    </div>
  </div>
</template>
