<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { GameWithStats, Platform, User } from "../../api.models";
import { TimeplayedAPI } from "../../api.client";
import RowV2 from "../ActivityRows/RowV2.vue";
const props = withDefaults(
  defineProps<{
    showExpand?: boolean;
    order?: "asc" | "desc";
    sort?: "recency" | "playtime" | "name" | "users";
    user?: User;
    platform?: Platform;
    limit?: number;
  }>(),
  {
    showExpand: false,
    order: "desc",
    sort: "recency",
    limit: 10,
  },
);

const _loadingPercent = ref(0);
const _gamesData = ref<GameWithStats[]>([]);
const _displayedGames = ref<GameWithStats[]>([]);
const loading = ref(false);
const localSort = ref(props.sort);
const localOrder = ref(props.order);
const _shownAmount = ref(props.limit || 10);

const SHOWN_INCREMENT = props.limit || 10;

async function fetchGames() {
  loading.value = true;
  _gamesData.value = [];
  _loadingPercent.value = 0;

  while (true) {
    const f = await TimeplayedAPI.getGames({
      limit: 100,
      offset: _gamesData.value.length,
      userId: props.user ? props.user.id : undefined,
      platformId: props.platform ? props.platform.id : undefined,
    });
    _gamesData.value.push(...f.data);
    if (_gamesData.value.length >= f.total) break;
    _loadingPercent.value = (_gamesData.value.length / f.total) * 100;
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
  } else if (localSort.value === "users") {
    _gamesData.value.sort((a, b) => {
      return localOrder.value === "asc"
        ? a.totals.user_count - b.totals.user_count
        : b.totals.user_count - a.totals.user_count;
    });
  }
  updateDisplayedGames();
}

/*watch([() => props.sort, () => props.order], ([newSort, newOrder]) => {
  localSort.value = newSort;
  localOrder.value = newOrder;
  sort();
});*/

function setSort(newSort: "recency" | "playtime" | "name" | "users") {
  console.log("sort", newSort);
  localSort.value = newSort;
  localOrder.value = localOrder.value == "asc" ? "desc" : "asc"; // flip
  sort();
}

onMounted(() => {
  fetchGames();
});
</script>

<template>
  <p v-if="loading" class="text-center text-muted">
    Loading... {{ _loadingPercent.toFixed(0) }}%
  </p>
  <template v-else-if="_gamesData.length > 0">
    <table class="table table table-hover table-responsive">
      <thead>
        <tr>
          <th></th>
          <th @click="setSort('name')">
            Game
            <i
              :class="
                localSort === 'name'
                  ? 'bi bi-sort-alpha-' +
                    (localOrder === 'asc' ? 'down' : 'up-alt')
                  : ''
              "
            />
          </th>
          <th @click="setSort('playtime')">
            Playtime
            <i
              :class="
                localSort === 'playtime'
                  ? 'bi bi-sort-' + (localOrder === 'asc' ? 'up-alt' : 'down')
                  : ''
              "
            />
          </th>
          <th @click="setSort('recency')">
            Last Played
            <i
              :class="
                localSort === 'recency'
                  ? 'bi bi-sort-' + (localOrder === 'asc' ? 'down' : 'up-alt')
                  : ''
              "
            />
          </th>

          <th @click="setSort('users')">
            Users
            <i
              :class="
                localSort === 'users'
                  ? 'bi bi-sort-' + (localOrder === 'asc' ? 'up-alt' : 'down')
                  : ''
              "
            />
          </th>
        </tr>
      </thead>
      <tbody>
        <RowV2
          v-for="game in _displayedGames"
          :key="game.game.id"
          :game="game"
          :context="'gameTable'"
          :durationSeconds="game.totals.playtime_secs"
          :date="
            game.newest_activity
              ? new Date(game.newest_activity.timestamp)
              : undefined
          "
        />
      </tbody>
    </table>
    <!--
    <GameRow v-for="game in _displayedGames" :key="game.game.id" :game="game" />-->

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
        {{ _displayedGames.length }} / {{ _gamesData.length }}
      </small>
    </div>
  </template>
  <div v-else class="text-center text-muted">No games found.</div>
</template>
