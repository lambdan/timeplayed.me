<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import GameRow from "./GameRow.vue";
import { cacheFetch, sleep } from "../../utils";
import ColorSpinners from "../Misc/ColorSpinners.vue";
import type { GameWithStats, PaginatedGamesWithStats, User } from "../../api.models";
const props = withDefaults(
  defineProps<{
    showExpand?: boolean;
    order?: "asc" | "desc";
    sort?: "recency" | "playtime" | "name";
    user?: User;
    limit?: number;
  }>(),
  {
    showExpand: false,
    order: "desc",
    sort: "recency",
    user: undefined,
    limit: 10,
  },
);

const limit = ref(props.limit);
const baseUrl = ref(`/api/games`);
const games = ref<GameWithStats[]>([]);
const displayedGames = ref<GameWithStats[]>([]);
const loading = ref(false);
const localSort = ref(props.sort);
const localOrder = ref(props.order);
const showAll = ref(false);

if (props.user) {
  baseUrl.value += `?userId=${props.user.id}`;
}

function getBaseUrl(): string {
  if (props.user) {
    return `/api/games?userId=${props.user.id}`;
  } else {
    return `/api/games`;
  }
}

async function fetchGames() {
  const CACHE_LIFETIME = 30_000;
  loading.value = true;
  games.value = [];

  const fetchedGames: GameWithStats[] = [];
  let res = await fetch(`${getBaseUrl()}`);
  console.log("Fetching games from", res.url);
  let data = (await res.json()) as PaginatedGamesWithStats;
  fetchedGames.push(...data.data);
  while (fetchedGames.length < data.total) {
    res = await cacheFetch(
      `${getBaseUrl()}${props.user ? `&` : `?`}offset=${fetchedGames.length}`,
      CACHE_LIFETIME,
    );
    console.log("Fetching games from", res.url);
    data = (await res.json()) as PaginatedGamesWithStats;
    fetchedGames.push(...data.data);
  }
  games.value = fetchedGames;
  sort();

  loading.value = false;
}

function updateDisplayedGames() {
  if (showAll.value || games.value.length <= limit.value || limit.value == 0) {
    displayedGames.value = games.value;
  } else {
    displayedGames.value = games.value.slice(0, limit.value);
  }
}

function sort() {
  if (localSort.value === "recency") {
    games.value.sort((a, b) => {
      if (!a.newest_activity || !b.newest_activity) return 0;
      return localOrder.value === "asc"
        ? a.newest_activity.timestamp - b.newest_activity.timestamp
        : b.newest_activity.timestamp - a.newest_activity.timestamp;
    });
  } else if (localSort.value === "playtime") {
    games.value.sort((a, b) => {
      return localOrder.value === "asc"
        ? a.totals.playtime_secs - b.totals.playtime_secs
        : b.totals.playtime_secs - a.totals.playtime_secs;
    });
  } else if (localSort.value === "name") {
    games.value.sort((a, b) => {
      const a_name = a.game.name;
      const b_name = b.game.name;
      return localOrder.value === "asc"
        ? a_name.localeCompare(b_name)
        : b_name.localeCompare(a_name);
    });
  }
  updateDisplayedGames();
}

watch([() => props.sort, () => props.order], ([newSort, newOrder]) => {
  localSort.value = newSort;
  localOrder.value = newOrder;
  sort();
});

onMounted(() => {
  limit.value = props.limit || 10;
  fetchGames();
});
</script>

<template>
  <ColorSpinners v-if="loading" />
  <template v-else-if="games.length > 0">
    <GameRow v-for="game in displayedGames" :key="game.game.id" :game="game" />

    <div class="text-center">
      <button
        v-if="!showAll && displayedGames.length < games.length"
        class="btn btn-primary"
        @click="
          showAll = true;
          updateDisplayedGames();
        "
      >
        Show All
      </button>
      <button
        v-else-if="showAll && limit > 0 && displayedGames.length > limit"
        class="btn btn-secondary"
        @click="
          showAll = false;
          updateDisplayedGames();
        "
      >
        Show Less
      </button>
    </div>
  </template>
  <div v-else class="text-center text-muted">No games found.</div>
</template>
