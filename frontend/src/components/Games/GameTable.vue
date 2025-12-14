<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import GameRow from "./GameRow.vue";
import ColorSpinners from "../Misc/ColorSpinners.vue";
import type { GameWithStats, User } from "../../api.models";
import { TimeplayedAPI } from "../../api.client";
const props = withDefaults(
  defineProps<{
    showExpand?: boolean;
    order?: "asc" | "desc";
    sort?: "recency" | "playtime" | "name";
    user?: User;
  }>(),
  {
    showExpand: false,
    order: "desc",
    sort: "recency",
  },
);

const _gamesData = ref<GameWithStats[]>([]);
const _displayedGames = ref<GameWithStats[]>([]);
const loading = ref(false);
const localSort = ref(props.sort);
const localOrder = ref(props.order);
const _shownAmount = ref(20);

const SHOWN_INCREMENT = 50;

async function fetchGames() {
  loading.value = true;
  _gamesData.value = [];

  while (true) {
    const f = await TimeplayedAPI.getGames({
      limit: 100,
      offset: _gamesData.value.length,
    });
    _gamesData.value.push(...f.data);
    if (_gamesData.value.length >= f.total) break;
  }
  sort();

  loading.value = false;
}

function updateDisplayedGames() {
  _shownAmount.value = Math.min(_shownAmount.value, _gamesData.value.length);
  _displayedGames.value = _gamesData.value.slice(0, _shownAmount.value);
}

function sort() {
  if (localSort.value === "recency") {
    _gamesData.value.sort((a, b) => {
      if (!a.newest_activity || !b.newest_activity) return 0;
      return localOrder.value === "asc"
        ? a.newest_activity.timestamp - b.newest_activity.timestamp
        : b.newest_activity.timestamp - a.newest_activity.timestamp;
    });
  } else if (localSort.value === "playtime") {
    _gamesData.value.sort((a, b) => {
      return localOrder.value === "asc"
        ? a.totals.playtime_secs - b.totals.playtime_secs
        : b.totals.playtime_secs - a.totals.playtime_secs;
    });
  } else if (localSort.value === "name") {
    _gamesData.value.sort((a, b) => {
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
  <template v-else-if="_gamesData.length > 0">
    <GameRow v-for="game in _displayedGames" :key="game.game.id" :game="game" />

    <div class="text-center">
      <button
        v-if="_displayedGames.length < _gamesData.length"
        class="btn btn-primary"
        @click="
          _shownAmount += SHOWN_INCREMENT;
          updateDisplayedGames();
        "
      >
        Show More
      </button>

      <small class="text-muted mt-2 d-block">
        {{ _displayedGames.length }} / {{ _gamesData.length }} games shown
      </small>
    </div>
  </template>
  <div v-else class="text-center text-muted">No games found.</div>
</template>
