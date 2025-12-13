<script setup lang="ts">
import { ref } from "vue";
import type { User } from "../../models/models";
import GameTable from "./GameTable.vue";
import SortOrderButtons from "../Misc/SortOrderButtons.vue";

const props = withDefaults(
  defineProps<{
    showExpand?: boolean;
    order?: "asc" | "desc";
    sort?: "recency" | "playtime" | "name";
    user?: User;
    limit: number;
  }>(),
  {
    showExpand: false,
    order: "desc",
    sort: "recency",
    user: undefined,
    limit: 10,
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
  <div class="col">
    <div class="card p-0">
      <h1 class="card-header">Games</h1>
      <div class="card-body">
        <SortOrderButtons
          :sort="localSort"
          :order="localOrder"
          :sortOptions="sortOptions"
          sortLabel="Sort Games"
          orderLabel="Order games"
          @update:sort="setSort"
          @update:order="setOrder"
        />
        <GameTable
          :sort="localSort"
          :order="localOrder"
          :user="props.user"
          :limit="props.limit"
        />
      </div>
    </div>
  </div>
</template>
