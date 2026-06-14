<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { GameWithStats, Platform, User } from "../../api.models";
import { TimeplayedAPI } from "../../api.client";
import RowV2 from "../ActivityRows/RowV2.vue";
import DateRangerPicker from "../Misc/DateRangerPicker.vue";

const props = withDefaults(
  defineProps<{
    showExpand?: boolean;
    order?: "asc" | "desc";
    sort?: "recency" | "playtime" | "name" | "users";
    user?: User;
    platform?: Platform;
    limit?: number;
    showDateRange?: boolean;
  }>(),
  {
    showExpand: false,
    order: "desc",
    sort: "playtime",
    limit: 10,
    showDateRange: true,
  },
);
const ONE_DAY = 24 * 60 * 60 * 1000;
// Set default starting millis to 7 days ago (speeds up fetching all games...)
// Default to all time on user/platform page
let _defaultStartingMillis = 7 * ONE_DAY;
if (props.user || props.platform) {
  _defaultStartingMillis = -1;
}

const _before = ref<Date | undefined>();
const _after = ref<Date | undefined>();
const _showDate = ref(props.showDateRange);
const _search = ref("");
const _showMore = ref(false);

const _gamesData = ref<GameWithStats[]>([]);
const _displayedGames = ref<GameWithStats[]>([]);
const loading = ref(false);
const localSort = ref(props.sort);
const localOrder = ref(props.order);
const _shownAmount = ref(props.limit || 10);

const SHOWN_INCREMENT = props.limit || 10;

/** Returns true if there is more */
async function fetchGames(limit = 10) {
  let order = localOrder.value;
  let sort = "playtime";
  if (localSort.value === "recency") {
    sort = "last_activity";
  } else if (localSort.value === "name") {
    sort = "name";
  } else if (localSort.value === "users") {
    sort = "user_count";
  }

  loading.value = true;
  const f = await TimeplayedAPI.getGamesStats({
    limit,
    offset: _gamesData.value.length,
    user: props.user ? props.user.id : undefined,
    platform: props.platform ? props.platform.id : undefined,
    before: _before.value ? _before.value.getTime() : undefined,
    after: _after.value ? _after.value.getTime() : undefined,
    search: _search.value.trim(),
    sort: sort as any,
    order: order as any,
  });

  _gamesData.value.push(...f);
  loading.value = false;

  updateDisplayedGames();
  if (f.length === 0 || f.length < limit) {
    _showMore.value = false;
    return false;
  } else {
    _showMore.value = true;
    return true;
  }
}

async function showMore() {
  _shownAmount.value += SHOWN_INCREMENT;
  fetchGames();
  updateDisplayedGames();
}

let searchTimeout: ReturnType<typeof setTimeout>;
function searchChange() {
  function reset() {
    _gamesData.value = [];
    _displayedGames.value = [];
  }
  clearTimeout(searchTimeout);
  const val = _search.value.trim();
  searchTimeout = setTimeout(() => {
    if (!val) {
      _search.value = "";
      reset();
      fetchGames();
      return;
    }
    if (val.length < 2) {
      return;
    }
    _search.value = val;
    reset();
    fetchGames();
  }, 200);
}

function updateDisplayedGames() {
  _displayedGames.value = _gamesData.value.slice(0, _shownAmount.value);
}

function setSort(newSort: "recency" | "playtime" | "name" | "users") {
  _showMore.value = false;
  _displayedGames.value = [];
  _gamesData.value = [];
  localSort.value = newSort;
  localOrder.value = localOrder.value == "asc" ? "desc" : "asc"; // flip
  fetchGames();
}

onMounted(() => {
  if (!props.showDateRange) {
    fetchGames();
  }
});
</script>

<template>
  <DateRangerPicker
    :toggleable="true"
    :relative-millis="_defaultStartingMillis"
    v-if="props.showDateRange"
    class="mb-2"
    @updated:both="
      ({ before, after, allTime, relativeMode }) => {
        console.log(
          'GameTable: date range updated',
          JSON.stringify(
            { before, after, allTime, relativeMode },
            undefined,
            4,
          ),
        );
        _before = before;
        _after = after;
        _showDate = allTime;
        if (!_showDate) {
          // change sort if recency was used
          if (localSort === 'recency') {
            localSort = 'playtime';
          }
        }
        searchChange();
      }
    "
  />
  <input
    v-model="_search"
    @input="searchChange()"
    type="text"
    class="form-control mb-2"
    placeholder="Search games..."
  />

  <p
    v-if="!loading && _displayedGames.length === 0"
    class="text-center text-muted"
  >
    Nothing found
  </p>

  <table
    class="table table table-hover table-responsive"
    v-if="_displayedGames.length > 0"
  >
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
        <th
          @click="setSort('recency')"
          v-if="_showDate"
          class="d-none d-md-table-cell"
        >
          Last Played
          <i
            :class="
              localSort === 'recency'
                ? 'bi bi-sort-' + (localOrder === 'asc' ? 'down' : 'up-alt')
                : ''
            "
          />
        </th>

        <th @click="setSort('users')" v-if="!props.user">
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
        :key="game.id"
        :showDate="_showDate"
        :game="game"
        :context="'gameTable'"
        :durationSeconds="game.stats.seconds"
        :date="
          game.stats.last_activity
            ? new Date(game.stats.last_activity)
            : undefined
        "
        :show-users="props.user ? false : true"
      />
    </tbody>
  </table>

  <div class="text-center" v-if="loading">
    <div class="spinner-border text-primary" role="status">
      <span class="visually-hidden">Loading...</span>
    </div>
  </div>

  <div class="text-center" v-if="_displayedGames.length > 0">
    <button
      class="btn btn-primary"
      @click="showMore()"
      v-if="_showMore && !loading"
    >
      Show More
    </button>

    <small class="text-muted mt-2 d-block">
      {{ _displayedGames.length }} games loaded
    </small>
  </div>
</template>
