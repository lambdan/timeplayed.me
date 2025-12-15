<script setup lang="ts">
import { ref } from "vue";
import GameTable from "./GameTable.vue";
import type { Platform, User } from "../../api.models";

const props = withDefaults(
  defineProps<{
    showExpand?: boolean;
    order?: "asc" | "desc";
    sort?: "recency" | "playtime" | "name";
    user?: User;
    platform?: Platform;
    showDateRange?: boolean;
    limit: number;
  }>(),
  {
    showExpand: false,
    order: "desc",
    sort: "recency",
    user: undefined,
    platform: undefined,
    limit: 10,
  },
);

const localSort = ref(props.sort);
const localOrder = ref(props.order);
</script>

<template>
  <div class="col">
    <div class="card p-0">
      <h1 class="card-header">Games</h1>
      <div class="card-body">
        <GameTable
          :sort="localSort"
          :order="localOrder"
          :user="props.user"
          :limit="props.limit"
          :platform="props.platform"
          :showDateRange="props.showDateRange"
        />
      </div>
    </div>
  </div>
</template>
