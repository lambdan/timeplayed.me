<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import PlatformRow from "./PlatformRow.vue";
import ColorSpinners from "../Misc/ColorSpinners.vue";
import { sleep } from "../../utils";
import type {
  Game,
  PaginatedPlatformsWithStats,
  PlatformWithStats,
  User,
} from "../../api.models";
const props = withDefaults(
  defineProps<{
    showExpand?: boolean;
    order?: "asc" | "desc";
    sort?: "recency" | "playtime" | "name";
    user?: User;
    game?: Game;
    showLastPlayed?: boolean;
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

const platforms = ref<PlatformWithStats[]>([]);
const loading = ref(false);
const localSort = ref(props.sort);
const localOrder = ref(props.order);

async function fetchPlatforms() {
  loading.value = true;
  platforms.value = [];
  const fetchedPlatforms: PlatformWithStats[] = [];
  let res = await fetch(`/api/platforms`);
  let data = (await res.json()) as PaginatedPlatformsWithStats;
  fetchedPlatforms.push(...data.data);

  while (fetchedPlatforms.length < data.total) {
    res = await fetch(`/api/platforms?offset=${fetchedPlatforms.length}`);
    data = (await res.json()) as PaginatedPlatformsWithStats;
    fetchedPlatforms.push(...data.data);
  }
  platforms.value = fetchedPlatforms;
  sort();
  loading.value = false;
}

async function fetchWithGame() {
  loading.value = true;
  platforms.value = [];
  const fetchedPlatforms: PlatformWithStats[] = [];
  let res = await fetch(`/api/platforms?gameId=${props.game?.id}`);
  let data = (await res.json()) as PaginatedPlatformsWithStats;
  fetchedPlatforms.push(...data.data);

  while (fetchedPlatforms.length < data.total) {
    res = await fetch(
      `/api/platforms?gameId=${props.game?.id}&offset=${fetchedPlatforms.length}`,
    );
    data = (await res.json()) as PaginatedPlatformsWithStats;
    fetchedPlatforms.push(...data.data);
  }
  platforms.value = fetchedPlatforms;
  sort();
  loading.value = false;
}

async function fetchWithUser() {
  loading.value = true;
  platforms.value = [];
  const fetchedPlatforms: PlatformWithStats[] = [];
  let res = await fetch(`/api/platforms?userId=${props.user?.id}`);
  let data = (await res.json()) as PaginatedPlatformsWithStats;
  fetchedPlatforms.push(...data.data);

  while (fetchedPlatforms.length < data.total) {
    res = await fetch(
      `/api/platforms?userId=${props.user?.id}&offset=${fetchedPlatforms.length}`,
    );
    data = (await res.json()) as PaginatedPlatformsWithStats;
    fetchedPlatforms.push(...data.data);
  }
  platforms.value = fetchedPlatforms;
  sort();
  loading.value = false;
}

function sort() {
  if (localSort.value === "recency") {
    platforms.value.sort((a, b) => {
      if (!a.newest_activity || !b.newest_activity) return 0;
      return localOrder.value === "asc"
        ? a.newest_activity.timestamp - b.newest_activity.timestamp
        : b.newest_activity.timestamp - a.newest_activity.timestamp;
    });
  } else if (localSort.value === "playtime") {
    platforms.value.sort((a, b) => {
      return localOrder.value === "asc"
        ? a.totals.playtime_secs - b.totals.playtime_secs
        : b.totals.playtime_secs - a.totals.playtime_secs;
    });
  } else if (localSort.value === "name") {
    platforms.value.sort((a, b) => {
      const a_name = a.platform.name || a.platform.abbreviation;
      const b_name = b.platform.name || b.platform.abbreviation;
      return localOrder.value === "asc"
        ? a_name.localeCompare(b_name)
        : b_name.localeCompare(a_name);
    });
  }
}

watch([() => props.sort, () => props.order], ([newSort, newOrder]) => {
  localSort.value = newSort;
  localOrder.value = newOrder;
  sort();
});

onMounted(() => {
  if (props.game) {
    fetchWithGame();
  } else if (props.user) {
    fetchWithUser();
  } else {
    fetchPlatforms();
  }
});
</script>

<template>
  <ColorSpinners v-if="loading" />
  <template v-else-if="platforms.length > 0">
    <PlatformRow
      v-for="platform in platforms"
      :key="platform.platform.id"
      :platform="platform"
      :showLastPlayed="props.showLastPlayed"
    />
  </template>
  <div v-else class="text-center text-muted">No platforms found.</div>
</template>
