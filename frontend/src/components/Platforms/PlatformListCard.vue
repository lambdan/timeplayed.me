<script setup lang="ts">
import { ref } from "vue";
import type { Game, User } from "../../models/models";
import PlatformTable from "./PlatformTable.vue";
import SortOrderButtons from "../Misc/SortOrderButtons.vue";

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

const sortOptions = [
  { value: "name", label: "Name" },
  { value: "recency", label: "Recency" },
  { value: "playtime", label: "Playtime" },
];

function setSort(newSort: string) {
  localSort.value = newSort as "recency" | "playtime" | "name";
}
function setOrder(newOrder: string) {
  localOrder.value = newOrder as "asc" | "desc";
}
</script>

<template>
  <div class="card p-0">
    <h1 class="card-header">Platforms</h1>
    <div class="card-body">
      <SortOrderButtons
        v-if="props.showSortButtons"
        :sort="localSort"
        :order="localOrder"
        :sortOptions="sortOptions"
        sortLabel="Sort platforms"
        orderLabel="Order platforms"
        @update:sort="setSort"
        @update:order="setOrder"
      />
      <PlatformTable
        :sort="localSort"
        :order="localOrder"
        :user="props.user"
        :game="props.game"
      />
    </div>
  </div>
</template>
