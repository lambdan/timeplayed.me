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

const loadingProgress = ref(0);

const loading = ref(false);
const localSort = ref(props.sort);
const localOrder = ref(props.order);
const localBefore = ref<Date | undefined>();
const localAfter = ref<Date | undefined>();
const showDateRange = ref<boolean>(props.showDateRange || false);
const startingRelativeDays = ref<number | undefined>(
  props.startingRelativeDays,
);

const _usersWithStats = ref<UserWithStats[]>([]);

async function fetchAllTheThings() {
  loadingProgress.value = 0;
  loading.value = false;
  _usersWithStats.value = [];

  while (true) {
    const f = await TimeplayedAPI.getUsers({
      limit: 100,
      offset: _usersWithStats.value.length,
      before: localBefore.value
        ? Math.floor(localBefore.value.getTime() / 1000)
        : undefined,
      after: localAfter.value
        ? Math.floor(localAfter.value.getTime() / 1000)
        : undefined,
    });
    _usersWithStats.value.push(...f.data);
    if (_usersWithStats.value.length >= f.total) break;
    loadingProgress.value = (_usersWithStats.value.length / f.total) * 100;
  }

  sortDisplayed();
  loading.value = false;
}

function sortDisplayed() {
  if (localSort.value === "recency") {
    _usersWithStats.value.sort((a, b) => {
      if (!a.newest_activity || !b.newest_activity) return 0;
      return localOrder.value === "asc"
        ? a.newest_activity.timestamp - b.newest_activity.timestamp
        : b.newest_activity.timestamp - a.newest_activity.timestamp;
    });
  } else if (localSort.value === "playtime") {
    _usersWithStats.value.sort((a, b) => {
      return localOrder.value === "asc"
        ? a.totals.playtime_secs - b.totals.playtime_secs
        : b.totals.playtime_secs - a.totals.playtime_secs;
    });
  } else if (localSort.value === "name") {
    _usersWithStats.value.sort((a, b) => {
      const a_name = a.user.name;
      const b_name = b.user.name;
      return localOrder.value === "asc"
        ? a_name.localeCompare(b_name)
        : b_name.localeCompare(a_name);
    });
  }
}

function setSort(newSort: "recency" | "playtime" | "name") {
  console.log("sort", newSort);
  localSort.value = newSort;
  localOrder.value = localOrder.value == "asc" ? "desc" : "asc"; // flip
  sortDisplayed();
}

onMounted(() => {
  if (!showDateRange.value) {
    fetchAllTheThings();
  } // else DateRange will trigger it
});
</script>

<template>
  <DateRangerPicker
    class="mb-2"
    v-if="showDateRange"
    @update:before="
      (val: Date | undefined) => {
        localBefore = val;
        fetchAllTheThings();
      }
    "
    @update:after="
      (val: Date | undefined) => {
        localAfter = val;
        fetchAllTheThings();
      }
    "
    :relativeDays="startingRelativeDays"
  />

  <!-- <ColorSpinners v-if="loading" /> -->
  <p v-if="loading" class="text-center">
    Loading... {{ loadingProgress.toFixed(0) }}%
  </p>

  <table v-if="!loading" class="table table table-hover table-responsive">
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
      </tr>
    </thead>
    <tbody>
      <RowV2
        v-for="user in _usersWithStats"
        :key="user.user.id"
        :user="user"
        :context="'userTable'"
        :durationSeconds="user.totals.playtime_secs"
        :date="
          user.newest_activity
            ? new Date(user.newest_activity.timestamp)
            : undefined
        "
      />
    </tbody>
  </table>
</template>
