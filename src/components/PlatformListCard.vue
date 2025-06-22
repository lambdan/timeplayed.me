<script setup lang="ts">
import { onMounted, ref } from "vue";
import GameTable from "./GameTable.vue";
import type { API_Platforms, Platform, User } from "../models/models";
import PlatformTable from "./PlatformTable.vue";

const props = withDefaults(
  defineProps<{
    limit?: number;
    showExpand?: boolean;
    order?: "asc" | "desc";
    sort?: "recency" | "playtime";
    user?: User;
  }>(),
  {
    limit: 25,
    showExpand: false,
    order: "desc",
    sort: "recency",
    user: undefined,
  }
);

const platforms = ref<Platform[]>([]);
const offset = ref(0);
const loading = ref(false);
const hasMore = ref(true);
const localSort = ref<"recency" | "playtime">(props.sort);
const localOrder = ref<"asc" | "desc">(props.order);

async function fetchPlatforms(limit?: number, offsetVal = 0) {
  const params = [];

  if (limit) {
    params.push(`limit=${limit}`);
  }
  if (offsetVal) {
    params.push(`offset=${offsetVal}`);
  }

  params.push(`sort=${localSort.value}`);
  params.push(`order=${localOrder.value}`);
  console.log(params);

  loading.value = true;

  console.log(props);
  let user = "";
  if (props.user) {
    user = `/users/${props.user.id}`;
  }

  const res = await fetch(`/api${user}/platforms?${params.join("&")}`);
  const data: API_Platforms = await res.json();

  const newPlatforms = data.data.map((platform: Platform) => ({
    ...platform,
  }));

  if (offsetVal === 0) {
    platforms.value = newPlatforms;
  } else {
    platforms.value = [...platforms.value, ...newPlatforms];
  }

  hasMore.value = data._total > offsetVal + newPlatforms.length;
  loading.value = false;
}

function loadMore() {
  offset.value += props.limit;
  fetchPlatforms(props.limit, offset.value);
}

function changeSort(newSort: "recency" | "playtime") {
  platforms.value = [];
  if (localSort.value !== newSort) {
    localSort.value = newSort;
    offset.value = 0;
    fetchPlatforms(props.limit, 0);
  }
}

function changeOrder(newOrder: "asc" | "desc") {
  platforms.value = [];
  if (localOrder.value !== newOrder) {
    localOrder.value = newOrder;
    offset.value = 0;
    fetchPlatforms(props.limit, 0);
  }
}

onMounted(() => {
  fetchPlatforms(props.limit, 0);
});
</script>

<template>
  <div class="card p-0">
    <h1 class="card-header">Platforms</h1>
    <div class="card-body">
      <!-- Sort Button Group -->
      <!--
      <div class="mb-3 text-center">
        <div class="btn-group" role="group" aria-label="Sort platforms">
          <button
            type="button"
            class="btn"
            :class="
              localSort === 'recency' ? 'btn-primary' : 'btn-outline-primary'
            "
            @click="changeSort('recency')"
          >
            Recency
          </button>
          <button
            type="button"
            class="btn"
            :class="
              localSort === 'playtime' ? 'btn-primary' : 'btn-outline-primary'
            "
            @click="changeSort('playtime')"
          >
            Playtime
          </button>
        </div>
      </div>-->
      <!-- Order Button Group -->
      <!---
      <div class="mb-3 text-center">
        <div class="btn-group" role="group" aria-label="Order platforms">
          <button
            type="button"
            class="btn"
            :class="
              localOrder === 'asc' ? 'btn-primary' : 'btn-outline-primary'
            "
            @click="changeOrder('asc')"
          >
            Ascending
          </button>
          <button
            type="button"
            class="btn"
            :class="
              localOrder === 'desc' ? 'btn-primary' : 'btn-outline-primary'
            "
            @click="changeOrder('desc')"
          >
            Descending
          </button>
        </div>
      </div>-->
      <div class="row table-responsive">
        <PlatformTable :platforms="platforms" :showExpand="props.showExpand" />
      </div>
      <div class="text-center my-2">
        <button v-if="loading" class="btn btn-primary" type="button" disabled>
          <span
            class="spinner-grow spinner-grow-sm"
            role="status"
            aria-hidden="true"
          ></span>
          Loading...
        </button>
        <button
          v-else-if="hasMore"
          class="btn btn-primary"
          :disabled="loading"
          @click="loadMore"
        >
          Load More
        </button>
      </div>
    </div>
  </div>
</template>
