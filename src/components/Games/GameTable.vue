<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import type { API_Games, GameWithStats, User } from "../../models/models";
import GameRow from "./GameRow.vue";
import { sleep } from "../../utils";
import ColorSpinners from "../Misc/ColorSpinners.vue";
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
  }
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
  baseUrl.value = `/api/users/${props.user.id}/games`;
}

async function fetchGames() {
  loading.value = true;
  games.value = [];

  const fetchedGames: GameWithStats[] = [];
  let res = await fetch(`${baseUrl.value}`);
  console.log("Fetching games from", res.url);
  let data = (await res.json()) as API_Games;
  fetchedGames.push(...data.data);
  while (fetchedGames.length < data._total) {
    res = await fetch(`${baseUrl.value}?offset=${fetchedGames.length}`);
    console.log("Fetching games from", res.url);
    data = (await res.json()) as API_Games;
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
      return localOrder.value === "asc"
        ? a.last_played - b.last_played
        : b.last_played - a.last_played;
    });
  } else if (localSort.value === "playtime") {
    games.value.sort((a, b) => {
      return localOrder.value === "asc"
        ? a.total_playtime - b.total_playtime
        : b.total_playtime - a.total_playtime;
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
  fetchGames();
});
</script>

<template>
  <ColorSpinners v-if="loading" />
  <template v-else-if="games.length > 0">
    <table class="table table-responsive table-hover">
      <thead>
        <tr>
          <th></th>
          <th>Name</th>
          <th>Last played</th>
          <th>Total playtime</th>
        </tr>
      </thead>
      <tbody>
        <GameRow
          v-for="game in displayedGames"
          :key="game.game.id"
          :game="game"
          :showExpand="props.showExpand"
        />
      </tbody>
    </table>
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
