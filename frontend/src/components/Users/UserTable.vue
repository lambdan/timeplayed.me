<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import DateRangerPicker from "../Misc/DateRangerPicker.vue";
import { fetchActivities, sleep } from "../../utils";

import UserRow from "./UserRow.vue";
import type {
  Activity,
  Game,
  PaginatedUsersWithStats,
  UserWithStats,
} from "../../api.models";
const props = withDefaults(
  defineProps<{
    game?: Game;
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
const localGame = ref(props.game);
const localBefore = ref<Date | undefined>();
const localAfter = ref<Date | undefined>();
const showDateRange = ref<boolean>(props.showDateRange || false);
const startingRelativeDays = ref<number | undefined>(
  props.startingRelativeDays,
);

const displayedUsers = ref<UserWithStats[]>([]);
const _usersWithStats = ref<UserWithStats[]>([]);

async function fetchAllTheThings() {
  if (loading.value) {
    return; // already running
  }
  loadingProgress.value = 0;
  loading.value = true;
  displayedUsers.value = [];
  _usersWithStats.value = [];

  let needToFetch = true;
  while (needToFetch) {
    const usersWithStatsBatch = await fetch(
      `/api/users?offset=${_usersWithStats.value.length}&limit=1`,
    );
    const usersWithStatsData =
      (await usersWithStatsBatch.json()) as PaginatedUsersWithStats;
    _usersWithStats.value.push(...usersWithStatsData.data);
    needToFetch = usersWithStatsData.total > _usersWithStats.value.length;
    loadingProgress.value = Math.min(
      100,
      (_usersWithStats.value.length / usersWithStatsData.total) * 100,
    );
  }

  displayedUsers.value = _usersWithStats.value;
  sortDisplayed();
  loading.value = false;
}

/*async function fetchAllTheThings() {
  if (loading.value) {
    return; // already running
  }
  loadingProgress.value = 0;
  loading.value = true;
  displayedUsers.value = [];
  const allActivity: Activity[] = [];

  let needToFetch = true;
  while (needToFetch) {
    const activities = await fetchActivities({
      before: localBefore.value,
      after: localAfter.value,
      limit: 200,
      offset: allActivity.length,
      gameId: localGame.value ? localGame.value.id.toString() : undefined,
    });
    allActivity.push(...activities.data);
    loadingProgress.value = Math.min(
      100,
      (allActivity.length / activities.total) * 100,
    );
    needToFetch = activities.total > allActivity.length;
  }

  // build UserWithStats
  const userMap: Map<string, UserWithStats> = new Map();
  for (const activity of allActivity) {
    const userId = activity.user.id;
    if (!userMap.has(userId)) {
      userMap.set(userId, {
        user: activity.user,
      });
    }
    const userStats = userMap.get(userId)!;
    userStats.total_playtime += activity.seconds;
    userStats.total_activities += 1;
    if (activity.timestamp > userStats.last_played) {
      userStats.last_played = activity.timestamp;
    }
  }

  for (const user of userMap.values()) {
    if (user.total_activities > 0) {
      displayedUsers.value.push(user);
    }
  }
  sortDisplayed();
  loading.value = false;
}*/

function sortDisplayed() {
  if (localSort.value === "recency") {
    displayedUsers.value.sort((a, b) => {
      if (!a.newest_activity || !b.newest_activity) return 0;
      return localOrder.value === "asc"
        ? a.newest_activity.timestamp - b.newest_activity.timestamp
        : b.newest_activity.timestamp - a.newest_activity.timestamp;
    });
  } else if (localSort.value === "playtime") {
    displayedUsers.value.sort((a, b) => {
      return localOrder.value === "asc"
        ? a.totals.playtime_secs - b.totals.playtime_secs
        : b.totals.playtime_secs - a.totals.playtime_secs;
    });
  } else if (localSort.value === "name") {
    displayedUsers.value.sort((a, b) => {
      const a_name = a.user.name;
      const b_name = b.user.name;
      return localOrder.value === "asc"
        ? a_name.localeCompare(b_name)
        : b_name.localeCompare(a_name);
    });
  }
}

watch([() => props.sort, () => props.order], ([newSort, newOrder]) => {
  localSort.value = newSort;
  localOrder.value = newOrder;
  sortDisplayed();
});

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

  <template v-else-if="displayedUsers.length > 0">
    <UserRow
      v-for="user in displayedUsers"
      :key="user.user.id"
      :user="user"
      :showExpand="props.showExpand"
      :showLastPlayed="props.showLastPlayed"
    />
  </template>
  <div v-else class="text-center text-muted">Nothing found</div>
</template>
