<script setup lang="ts">
import { ref } from "vue";
import PlatformTable from "./PlatformTable.vue";
import type { Game, User } from "../../api.models";

const props = withDefaults(
  defineProps<{
    order?: "asc" | "desc";
    sort?: "recency" | "playtime" | "name";
    user?: User;
    game?: Game;
    showSortButtons?: boolean;
  }>(),
  {
    order: "desc",
    sort: "recency",
    user: undefined,
    game: undefined,
    showSortButtons: true,
  },
);

const localSort = ref(props.sort);
const localOrder = ref(props.order);
</script>

<template>
  <div class="card p-0">
    <h1 class="card-header">Platforms</h1>
    <div class="card-body">
      <PlatformTable
        :sort="localSort"
        :order="localOrder"
        :user="props.user"
        :game="props.game"
      />
    </div>
  </div>
</template>
