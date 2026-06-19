<script setup lang="ts">
import { onMounted, ref } from "vue";
import DateRangerPicker from "../Misc/DateRangerPicker.vue";
import type { UserWithStats } from "../../api.models";
import { TimeplayedAPI } from "../../api.client";
import RowV2 from "../ActivityRows/RowV2.vue";
const props = withDefaults(
  defineProps<{
    showExpand?: boolean;
    order?: "asc" | "desc";
    sort?: "recency" | "playtime" | "name";
    showDateRange?: boolean;
    startingRelativeDays?: number;
    showLastPlayed?: boolean;
  }>(),
  {
    showExpand: false,
    order: "desc",
    sort: "recency",
    game: undefined,
    showLastPlayed: true,
  },
);

const _before = ref<Date | undefined>();
const _after = ref<Date | undefined>();
const _showDate = ref(props.showDateRange);

const loading = ref(true);
const localSort = ref(props.sort);
const localOrder = ref(props.order);

const _usersWithStats = ref<UserWithStats[]>([]);

const _search = ref("");
const _searchInput = ref("");
let searchTimeout: ReturnType<typeof setTimeout>;
function searchChange() {
  clearTimeout(searchTimeout);
  const val = _searchInput.value.trim();
  searchTimeout = setTimeout(() => {
    if (!val) {
      _search.value = "";
      fetchUsers();
      return;
    }
    if (val.length < 2) {
      return;
    }
    _search.value = val;
    fetchUsers();
  }, 200);
}

async function fetchUsers() {
  loading.value = true;
  _usersWithStats.value = [];

  const order = localOrder.value;
  let sort = "playtime";
  if (localSort.value === "recency") {
    sort = "last_activity";
  } else if (localSort.value === "name") {
    sort = "name";
  }

  let offset = 0;
  const limit = 100;
  while (true) {
    const f = await TimeplayedAPI.getUsersStats({
      offset,
      before: _before.value?.getTime(),
      after: _after.value?.getTime(),
      order,
      sort: sort as any,
      limit,
      search: _search.value.trim(),
    });
    for (const u of f) {
      offset += 1;
      // only include users with playtime
      if (u.stats.seconds === 0) {
        continue;
      }
      _usersWithStats.value.push(u);
    }
    if (f.length === 0 || f.length < limit) {
      break;
    }
  }

  loading.value = false;
}

function setSort(newSort: "recency" | "playtime" | "name") {
  localSort.value = newSort;
  localOrder.value = localOrder.value == "asc" ? "desc" : "asc"; // flip
  fetchUsers();
}

onMounted(() => {
  if (!props.showDateRange) {
    fetchUsers();
  }
});
</script>

<template>
  <DateRangerPicker
    :relativeMillis="30 * 24 * 60 * 60 * 1000"
    :toggleable="true"
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
    v-model="_searchInput"
    @input="searchChange()"
    type="text"
    class="form-control mb-2"
    placeholder="Search users..."
  />

  <table
    v-if="_usersWithStats.length > 0"
    class="table table table-hover table-responsive"
  >
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
          v-if="_after === undefined && props.showLastPlayed"
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
      </tr>
    </thead>
    <tbody>
      <RowV2
        v-for="user in _usersWithStats"
        :key="user.id"
        :userWithStats="user"
        :showDate="_after === undefined && props.showLastPlayed"
        :context="'userTable'"
        :durationSeconds="user.stats.seconds"
        :date="
          user.stats.last_activity
            ? new Date(user.stats.last_activity)
            : undefined
        "
        :showUsers="false"
      />
    </tbody>
  </table>
  <div class="text-center" v-if="loading">
    <div class="spinner-border text-primary" role="status">
      <span class="visually-hidden">Loading...</span>
    </div>
  </div>
</template>
