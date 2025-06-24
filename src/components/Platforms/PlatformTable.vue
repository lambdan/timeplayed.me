<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import type {
  API_Platforms,
  Game,
  PlatformWithStats,
  User,
} from "../../models/models";
import PlatformRow from "./PlatformRow.vue";
import ColorSpinners from "../Misc/ColorSpinners.vue";
import { sleep } from "../../utils";
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
  }
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
  let data = (await res.json()) as API_Platforms;
  fetchedPlatforms.push(...data.data);

  while (fetchedPlatforms.length < data._total) {
    res = await fetch(`/api/platforms?offset=${fetchedPlatforms.length}`);
    data = (await res.json()) as API_Platforms;
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
  let res = await fetch(`/api/games/${props.game?.id}/platforms`);
  let data = (await res.json()) as PlatformWithStats[];
  fetchedPlatforms.push(...data);

  platforms.value = fetchedPlatforms;
  sort();
  loading.value = false;
}

function sort() {
  if (localSort.value === "recency") {
    platforms.value.sort((a, b) => {
      return localOrder.value === "asc"
        ? a.last_played - b.last_played
        : b.last_played - a.last_played;
    });
  } else if (localSort.value === "playtime") {
    platforms.value.sort((a, b) => {
      return localOrder.value === "asc"
        ? a.total_playtime - b.total_playtime
        : b.total_playtime - a.total_playtime;
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
  } else {
    fetchPlatforms();
  }
});
</script>

<template>
  <ColorSpinners v-if="loading" />
  <template v-else-if="platforms.length > 0">
    <table class="table table-responsive table-hover">
      <thead>
        <tr>
          <th>Name</th>
          <th v-if="showLastPlayed">Last played</th>
          <th>Total playtime</th>
        </tr>
      </thead>
      <tbody>
        <PlatformRow
          v-for="platform in platforms"
          :key="platform.platform.id"
          :platform="platform"
          :showExpand="props.showExpand"
          :showLastPlayed="props.showLastPlayed"
        />
      </tbody>
    </table>
  </template>
  <div v-else class="text-center text-muted">No platforms found.</div>
</template>
