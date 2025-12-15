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

const _loadingPercent = ref(0);
const _platformsData = ref<PlatformWithStats[]>([]);
const loading = ref(false);
const localSort = ref(props.sort);
const localOrder = ref(props.order);

async function fetchPlatforms() {
  if (loading.value) return;
  loading.value = true;
  _platformsData.value = [];
  _loadingPercent.value = 0;
  while (true) {
    const fetchedPlatfomrs = await TimeplayedAPI.getPlatforms({
      limit: 100,
      offset: _platformsData.value.length,
      userId: props.user ? props.user.id : undefined,
      gameId: props.game ? props.game.id : undefined,
      before: _before.value ? Math.floor(_before.value.getTime()) : undefined,
      after: _after.value ? Math.floor(_after.value.getTime()) : undefined,
    });
    _platformsData.value.push(...fetchedPlatfomrs.data);
    if (_platformsData.value.length >= fetchedPlatfomrs.total) break;
    _loadingPercent.value =
      (_platformsData.value.length / fetchedPlatfomrs.total) * 100;
  }
  sort();
  loading.value = false;
}

function sort() {
  if (localSort.value === "recency") {
    _platformsData.value.sort((a, b) => {
      if (!a.newest_activity || !b.newest_activity) return 0;
      return localOrder.value === "asc"
        ? a.newest_activity.timestamp - b.newest_activity.timestamp
        : b.newest_activity.timestamp - a.newest_activity.timestamp;
    });
  } else if (localSort.value === "playtime") {
    _platformsData.value.sort((a, b) => {
      return localOrder.value === "asc"
        ? a.totals.playtime_secs - b.totals.playtime_secs
        : b.totals.playtime_secs - a.totals.playtime_secs;
    });
  } else if (localSort.value === "name") {
    _platformsData.value.sort((a, b) => {
      const a_name = a.platform.name || a.platform.abbreviation;
      const b_name = b.platform.name || b.platform.abbreviation;
      return localOrder.value === "asc"
        ? a_name.localeCompare(b_name)
        : b_name.localeCompare(a_name);
    });
  } else if (localSort.value === "users") {
    _platformsData.value.sort((a, b) => {
      return localOrder.value === "asc"
        ? a.totals.user_count - b.totals.user_count
        : b.totals.user_count - a.totals.user_count;
    });
  }
}

function setSort(newSort: "recency" | "playtime" | "name" | "users") {
  console.log("sort", newSort);
  localSort.value = newSort;
  localOrder.value = localOrder.value == "asc" ? "desc" : "asc"; // flip
  sort();
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
        fetchPlatforms();
      }
    "
  />

  <p v-if="loading" class="text-center text-muted">
    Loading... {{ _loadingPercent.toFixed(0) }}%
  </p>
  <template v-else-if="_platformsData.length > 0">
    <table class="table table table-hover table-responsive">
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
          :key="platform.platform.id"
          :platform="platform"
          :context="'platformTable'"
          :durationSeconds="platform.totals.playtime_secs"
          :date="
            platform.newest_activity
              ? new Date(platform.newest_activity.timestamp)
              : undefined
          "
          :showDate="true"
          :showUsers="props.user ? false : true"
        />
      </tbody>
    </table>

    <!--
  <ColorSpinners v-if="loading" />
  <template v-else-if="platforms.length > 0">
    <PlatformRow
      v-for="platform in platforms"
      :key="platform.platform.id"
      :platform="platform"
      :showLastPlayed="props.showLastPlayed"
    />
  </template>
  <div v-else class="text-center text-muted">No platforms found.</div> -->
  </template>
</template>
