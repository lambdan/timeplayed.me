<script setup lang="ts">
import { ref } from "vue";
import type { Game, User } from "../../models/models";
import UserTable from "./UserTable.vue";

const props = withDefaults(
  defineProps<{
    game?: Game;
    startingRelativeDays?: number;
  }>(),
  {
    game: undefined,
    startingRelativeDays: undefined
  }
);
</script>

<template>
  <div class="card p-0">
    <h2 class="card-header">Top players</h2>
    <div class="card-body">
      <UserTable 
        :game="game" 
        :sort="'playtime'" 
        :order="'desc'" 
        :show-date-range="true" 
        :starting-relative-days="props.startingRelativeDays" 
        :show-last-played="false" />
    </div>
  </div>
</template>
