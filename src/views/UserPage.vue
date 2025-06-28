<script setup lang="ts">
import { onMounted, ref } from "vue";
import GameListCard from "../components/Games/GameListCard.vue";
import UserInfoCard from "../components/UserInfoCard.vue";
import RecentActivityCard from "../components/RecentActivityCard.vue";
import { type UserWithStats } from "../models/models";
import { useRoute } from "vue-router";
import PlaytimeChart from "../components/Charts/PlaytimeChart.vue";
import PlatformTable from "../components/Platforms/PlatformTable.vue";

const route = useRoute();
const apiUser = ref<UserWithStats>();

// Toggle state for cards (activity, playtime, games, platforms)
const showActivity = ref(true);
const showPlaytime = ref(false);
const showGames = ref(false);
const showPlatforms = ref(false);

function toggleCard(card: "activity" | "playtime" | "games" | "platforms") {
  showActivity.value = card === "activity";
  showPlaytime.value = card === "playtime";
  showGames.value = card === "games";
  showPlatforms.value = card === "platforms";
}

onMounted(async () => {
  const userId = route.params.id as string;
  const userRes = await fetch(`/api/users/${userId}`);
  apiUser.value = await userRes.json();
});
</script>

<template>
  <UserInfoCard class="mb-4" v-if="apiUser" :user="apiUser.user" />
  <div class="mb-3 d-flex justify-content-center gap-2" v-if="apiUser">
    <button
      class="btn btn-outline-primary"
      :class="{ active: showActivity }"
      @click="toggleCard('activity')"
    >
      Recent Activity
    </button>
    <button
      class="btn btn-outline-primary"
      :class="{ active: showGames }"
      @click="toggleCard('games')"
    >
      All Games
    </button>
    <button
      class="btn btn-outline-primary"
      :class="{ active: showPlaytime }"
      @click="toggleCard('playtime')"
    >
      Chart
    </button>
    <button
      class="btn btn-outline-primary"
      :class="{ active: showPlatforms }"
      @click="toggleCard('platforms')"
    >
      Platforms
    </button>
  </div>
  <RecentActivityCard
    v-if="apiUser && showActivity"
    :limit="5"
    :user="apiUser.user"
    :showExpand="true"
    class="mb-4"
  />
  <div class="card mt-4 p-0 mb-4" v-if="apiUser && showPlaytime">
    <h1 class="card-header">Playtime</h1>
    <PlaytimeChart :user="apiUser.user" />
  </div>
  <GameListCard
    v-if="apiUser && showGames"
    class="mb-4"
    :showExpand="false"
    :limit="5"
    :order="'desc'"
    :sort="'playtime'"
    :user="apiUser.user"
  ></GameListCard>
  <div class="card mt-4 p-0 mb-4" v-if="apiUser && showPlatforms">
    <h1 class="card-header">Platforms</h1>
    <div class="card-body">
      <PlatformTable
        :user="apiUser.user"
        :sort="'playtime'"
        :order="'desc'"
        :showLastPlayed="false"
      />
    </div>
  </div>
</template>
