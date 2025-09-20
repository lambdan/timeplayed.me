<script setup lang="ts">
import { onMounted, ref } from "vue";
import RecentActivityCard from "../components/RecentActivityCard.vue";
import {
  type API_Platforms,
  type GameWithStats,
  type PlatformWithStats,
} from "../models/models";
import { useRoute } from "vue-router";
import GameInfoCard from "../components/GameInfoCard.vue";
import TopPlayersCard from "../components/Users/TopPlayersCard.vue";
import PlaytimeChart from "../components/Charts/PlaytimeChart.vue";
import PlatformInfoCard from "../components/PlatformInfoCard.vue";
import ColorSpinners from "../components/Misc/ColorSpinners.vue";

const route = useRoute();
const platform = ref<PlatformWithStats>();

const platforms = ref<PlatformWithStats[]>([]);
const loading = ref(false);

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
  loading.value = false;
}

onMounted(async () => {
  await fetchPlatforms();
  const platformId = +(route.params.id as string);
  console.log("PLATFORM ID", platformId);
  const selected = platforms.value.find((p) => p.platform.id === platformId);
  if (selected) {
    platform.value = selected;
  }
});
</script>

<template>
  <div v-if="!platform">
    <ColorSpinners />
  </div>
  <div v-else>
    <PlatformInfoCard class="mb-4" :platform="platform" />
  </div>
</template>
