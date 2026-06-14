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

async function fetchPlatforms() {
  loading.value = true;
  const fetched = await TimeplayedAPI.getPlatformsStats({
    limit: 100,
    offset: _platformsData.value.length,
    user: props.user ? props.user.id : undefined,
    game: props.game ? props.game.id : undefined,
    before: _before.value ? _before.value.getTime() : undefined,
    after: _after.value ? _after.value.getTime() : undefined,
  });
  _platformsData.value.push(...fetched);
  loading.value = false;
}

function setSort(newSort: "recency" | "playtime" | "name" | "users") {
  console.log("sort", newSort);
  localSort.value = newSort;
  localOrder.value = localOrder.value == "asc" ? "desc" : "asc"; // flip
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
        fetchPlatforms();
      }
    "
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
          :platform="platform"
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

  <div v-if="loading" class="text-muted">
    <span
      class="spinner-grow spinner-grow-sm"
      role="status"
      aria-hidden="true"
    ></span>
    Loading...
  </div>
</template>
