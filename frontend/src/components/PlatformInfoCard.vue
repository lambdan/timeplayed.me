<script setup lang="ts">
import { onMounted, ref } from "vue";
import {
  type PlatformWithStats,
  type Game,
  type GameStats,
  type Platform,
  type Activity,
  type API_Platforms,
} from "../models/models";
import { formatDate, formatDuration, sleep, timeAgo } from "../utils";
import GameCover from "./Games/GameCover.vue";
import PlatformListCard from "./Platforms/PlatformListCard.vue";
import PlatformTable from "./Platforms/PlatformTable.vue";

const props = defineProps<{ platform: PlatformWithStats }>();

const activities = ref<Activity[]>([]);
const platform = ref<PlatformWithStats>();
const loadingStats = ref(true);

// Collapse state for each column
/*
const showStats = ref(true);
const showMetadata = ref(false);
const showPlatforms = ref(false);

function toggleColumn(column: "stats" | "metadata" | "platforms") {
  showStats.value = column === "stats";
  showMetadata.value = column === "metadata";
  showPlatforms.value = column === "platforms";
}*/

onMounted(async () => {
  platform.value = props.platform;
  const res = await fetch(
    `/api/activities?platform=${props.platform.platform.id}&limit=1000`,
  );
  const data = (await res.json()) as Activity[];
  console.log("DATA", data);
  activities.value = data;
  loadingStats.value = false;
});
</script>

<template>
  <div v-if="platform" class="card p-0">
    <h1 class="card-header">
      {{ platform.platform.name }}
      <!--<span class="text-muted">
        {{ platform.platform.abbreviation }}
      </span>-->
    </h1>
    <div class="card-body">
      <div class="row">
        <div
          class="col-12 col-lg-auto d-flex flex-column align-items-center justify-content-center mb-3 mb-lg-0"
        ></div>
      </div>
    </div>
  </div>
</template>
