<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import DateRangerPicker from "../Misc/DateRangerPicker.vue";
import { fetchActivities, sleep } from "../../utils";
import type { Activity, API_Activities, API_Users, Game, UserWithStats } from "../../models/models";
import UserRow from "./UserRow.vue";
const props = withDefaults(
  defineProps<{
    game?: Game;
    showExpand?: boolean;
    order?: "asc" | "desc";
    sort?: "recency" | "playtime" | "name";
    showDateRange?: boolean;
    startingRelativeDays?: number;
  }>(),
  {
    showExpand: false,
    order: "desc",
    sort: "recency",
    game: undefined,
  }
);

const loadingProgress = ref(0);
const displayedUsers = ref<UserWithStats[]>([]);
const loading = ref(false);
const localSort = ref(props.sort);
const localOrder = ref(props.order);
const localGame = ref(props.game);
const localBefore = ref<Date|undefined>();
const localAfter = ref<Date|undefined>();
const showDateRange = ref<boolean>(props.showDateRange || false);
const startingRelativeDays = ref<number|undefined>(props.startingRelativeDays);

async function fetchAllTheThings() {
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
      limit: 500,
      offset: allActivity.length,
      gameId: localGame.value ? localGame.value.id.toString() : undefined,
    });
    allActivity.push(...activities.data);
    loadingProgress.value = Math.min(
      100,
      (allActivity.length / activities._total) * 100
    );
    needToFetch = activities._total > allActivity.length;
  }

  // build UserWithStats
  const userMap: Map<number, UserWithStats> = new Map();
  for (const activity of allActivity) {
    const userId = activity.user.id;
    if (!userMap.has(userId)) {
      userMap.set(userId, {
        user: activity.user,
        total_playtime: 0,
        last_played: 0,
        total_activities: 0
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
}

function sortDisplayed() {
  if (localSort.value === "recency") {
    displayedUsers.value.sort((a, b) => {
      return localOrder.value === "asc"
        ? a.last_played - b.last_played
        : b.last_played - a.last_played;
    });
  } else if (localSort.value === "playtime") {
    displayedUsers.value.sort((a, b) => {
      return localOrder.value === "asc"
        ? a.total_playtime - b.total_playtime
        : b.total_playtime - a.total_playtime;
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
  <DateRangerPicker class="mb-2" v-if="showDateRange"
    @update:before="(val: Date) => { localBefore = val; fetchAllTheThings(); }"
    @update:after="(val: Date) => { localAfter = val; fetchAllTheThings(); }"
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
    />
  </template>
  <div v-else class="text-center text-muted">Nothing found</div>
</template>
