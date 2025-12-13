<script setup lang="ts">
import { ref } from "vue";
import type { User } from "../../models/models";
import UserTable from "./UserTable.vue";
import SortOrderButtons from "../Misc/SortOrderButtons.vue";

const props = withDefaults(
  defineProps<{
    showExpand?: boolean;
    order?: "asc" | "desc";
    sort?: "recency" | "playtime" | "name";
  }>(),
  {
    showExpand: false,
    order: "desc",
    sort: "recency",
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
    <h1 class="card-header">Users</h1>
    <div class="card-body">
      <SortOrderButtons
        :sort="localSort"
        :order="localOrder"
        :sortOptions="sortOptions"
        sortLabel="Sort users"
        orderLabel="Order users"
        @update:sort="setSort"
        @update:order="setOrder"
      />
      <UserTable
        :showExpand="props.showExpand"
        :sort="localSort"
        :order="localOrder"
        :showDateRange="false"
      />
    </div>
  </div>
</template>
