<script setup lang="ts">
import { onMounted, ref } from "vue";
import GameTable from "./GameTable.vue";
import type { API_Games, Game, User } from "../models/models";

const props = withDefaults(
  defineProps<{
    limit?: number;
    showExpand?: boolean;
    order?: "asc" | "desc";
    sort?: "recency" | "playtime" | "name";
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

const games = ref<Game[]>([]);
const offset = ref(0);
const loading = ref(false);
const hasMore = ref(true);
const localSort = ref<"recency" | "playtime" | "name">(props.sort);
const localOrder = ref<"asc" | "desc">(props.order);

async function fetchGames(limit?: number, offsetVal = 0) {
  const params = [];

  if (limit) {
    params.push(`limit=${limit}`);
  }
  if (offsetVal) {
    params.push(`offset=${offsetVal}`);
  }
  if (props.user) {
    params.push(`user=${props.user.id}`);
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

  const res = await fetch(`/api${user}/games?${params.join("&")}`);
  const data: API_Games = await res.json();

  const newGames = data.data.map((game: Game) => ({
    ...game,
  }));

  if (offsetVal === 0) {
    games.value = newGames;
  } else {
    games.value = [...games.value, ...newGames];
  }

  hasMore.value = data._total > offsetVal + newGames.length;
  loading.value = false;
}

function loadMore() {
  offset.value += props.limit;
  fetchGames(props.limit, offset.value);
}

function changeSort(newSort: "recency" | "playtime" | "name") {
  games.value = [];
  if (localSort.value !== newSort) {
    localSort.value = newSort;
    offset.value = 0;
    fetchGames(props.limit, 0);
  }
}

function changeOrder(newOrder: "asc" | "desc") {
  games.value = [];
  if (localOrder.value !== newOrder) {
    localOrder.value = newOrder;
    offset.value = 0;
    fetchGames(props.limit, 0);
  }
}

onMounted(() => {
  fetchGames(props.limit, 0);
});
</script>

<template>
  <div class="card p-0">
    <h1 class="card-header">Games</h1>
    <div class="card-body">
      <!-- Sort Button Group -->
      <div class="mb-3 text-center">
        <div class="btn-group" role="group" aria-label="Sort games">
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
          <button
            type="button"
            class="btn"
            :class="
              localSort === 'name' ? 'btn-primary' : 'btn-outline-primary'
            "
            @click="changeSort('name')"
          >
            Name
          </button>
        </div>
      </div>
      <!-- Order Button Group -->
      <div class="mb-3 text-center">
        <div class="btn-group" role="group" aria-label="Order games">
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
      </div>
      <div class="row table-responsive">
        <GameTable :games="games" :showExpand="props.showExpand" />
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
