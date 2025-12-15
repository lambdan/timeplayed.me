<script setup lang="ts">
import { ref } from "vue";
import UserTable from "./UserTable.vue";

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
</script>

<template>
  <div class="card p-0">
    <h1 class="card-header">Users</h1>
    <div class="card-body">
      <UserTable
        :showExpand="props.showExpand"
        :sort="localSort"
        :order="localOrder"
        :showDateRange="false"
      />
    </div>
  </div>
</template>
