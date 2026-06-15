<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { Game, PlatformWithStats, User } from "../../api.models";
import { TimeplayedAPI } from "../../api.client";
import RowV2 from "../ActivityRows/RowV2.vue";
import DateRangerPicker from "../Misc/DateRangerPicker.vue";

const props = withDefaults(
  defineProps<{
    showExpand?: boolean;
    order?: "asc" | "desc";
    sort?: "recency" | "playtime" | "name" | "users";
    user?: User;
    game?: Game;
    showLastPlayed?: boolean;
    showDateRange?: boolean;
  }>(),
  {
    showExpand: false,
    order: "desc",
    sort: "recency",
    user: undefined,
    game: undefined,
    showLastPlayed: true,
  },
);

const _before = ref<Date | undefined>();
const _after = ref<Date | undefined>();
const _showDate = ref(props.showDateRange);

const _platformsData = ref<PlatformWithStats[]>([]);
const loading = ref(true);
const localSort = ref(props.sort);
const localOrder = ref(props.order);

const _search = ref("");
let searchTimeout: ReturnType<typeof setTimeout>;
function searchChange() {
  clearTimeout(searchTimeout);
  const val = _search.value.trim();
  searchTimeout = setTimeout(() => {
    if (!val) {
      _search.value = "";
      fetchPlatforms();
      return;
    }
    if (val.length < 2) {
      return;
    }
    _search.value = val;
    fetchPlatforms();
  }, 200);
}

async function fetchPlatforms() {
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
  _platformsData.value = [];
  const limit = 100;
  while (true) {
    const fetched = await TimeplayedAPI.getPlatformsStats({
      limit,
      offset: _platformsData.value.length,
      user: props.user ? props.user.id : undefined,
      game: props.game ? props.game.id : undefined,
      before: _before.value ? _before.value.getTime() : undefined,
      after: _after.value ? _after.value.getTime() : undefined,
      order,
      sort: sort as any,
      search: _search.value.trim(),
    });
    _platformsData.value.push(...fetched);
    if (fetched.length === 0 || fetched.length < limit) {
      break;
    }
  }
  loading.value = false;
}

function setSort(newSort: "recency" | "playtime" | "name" | "users") {
  console.log("sort", newSort);
  localSort.value = newSort;
  localOrder.value = localOrder.value == "asc" ? "desc" : "asc"; // flip
  fetchPlatforms();
}

onMounted(() => {
  if (!props.showDateRange) {
    fetchPlatforms();
  }
});
</script>

<template>
  <DateRangerPicker
    :toggleable="true"
    :relativeMillis="-1"
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
  <!-- show search box if not filtering by user or game (ie only on platform list page) -->
  <input
    v-if="!props.user && !props.game"
    v-model="_search"
    @input="searchChange()"
    type="text"
    class="form-control mb-2"
    placeholder="Search platforms..."
  />

  <template v-if="_platformsData.length > 0">
    <table class="table table-hover table-responsive">
      <thead>
        <tr>
          <th></th>
          <th @click="setSort('name')">
            Name
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
            v-if="_after === undefined && _showDate"
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
          v-for="platform in _platformsData"
          :key="platform.id"
          :platformWithStats="platform"
          :context="'platformTable'"
          :durationSeconds="platform.stats.seconds"
          :date="
            platform.stats.last_activity
              ? new Date(platform.stats.last_activity)
              : undefined
          "
          :showDate="_after === undefined"
          :showUsers="props.user ? false : true"
        />
      </tbody>
    </table>
  </template>

  <div class="text-center" v-if="loading">
    <div class="spinner-border text-primary" role="status">
      <span class="visually-hidden">Loading...</span>
    </div>
  </div>
</template>
