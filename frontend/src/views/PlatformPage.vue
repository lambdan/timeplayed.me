<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import type { Platform, PlatformWithStats } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import AdminEditLink from "../components/Misc/AdminEditLink.vue";
import InfoStatTiles from "../components/Misc/InfoStatTiles.vue";
import {
  platformBackground,
  platformIcon,
  platformTextColor,
} from "../platformStyle";
import YourStatsCard from "../components/Users/YourStatsCard.vue";
import TopGamesList from "../components/Games/TopGamesList.vue";
import TopPlayersCard from "../components/Users/TopPlayersCard.vue";
import RecentActivityCard from "../components/RecentActivityCard.vue";
import DateRangerPicker from "../components/Misc/DateRangerPicker.vue";
import PlaytimeCharts from "../components/Charts/PlaytimeCharts.vue";
import ChildPlatformsCard from "../components/Platforms/ChildPlatformsCard.vue";
import { usePageTitle } from "../composables/usePageTitle";

const route = useRoute();
const setTitle = usePageTitle();
const platform = ref<PlatformWithStats>();
// stats including all child platforms, only fetched for platforms with children
const familyStats = ref<PlatformWithStats["stats"]>();
const parent = ref<Platform>();
// the whole page includes the child platforms
const withChildren = computed(
  () => (platform.value?.children_ids.length ?? 0) > 0,
);
const stats = computed(() => familyStats.value ?? platform.value?.stats);
// date range for the top lists next to recent activity, set by their picker
const topAfter = ref<Date>();
const topBefore = ref<Date>();
// lists wait for the pickers first range
const topReady = ref(false);

onMounted(async () => {
  const platformId = parseInt(route.params.id as string);
  const loaded = await TimeplayedAPI.getPlatformStats(platformId);
  // before showing the page, so the numbers don't change after a moment
  if (loaded.children_ids.length > 0) {
    const family = await TimeplayedAPI.getPlatformStats(platformId, {
      include_child_platforms: true,
    });
    familyStats.value = family.stats;
  }
  if (loaded.parent_id) {
    parent.value = await TimeplayedAPI.getPlatform(loaded.parent_id);
  }
  platform.value = loaded;
  setTitle(`${platform.value.display_name} playtime`);
});
</script>

<template>
  <div v-if="!platform || !stats" class="text-center">
    <div class="spinner-border" role="status"></div>
  </div>

  <template v-else>
    <div class="row g-4">
      <!-- own row, so the info card is full width when the user's stats are hidden -->
      <div class="col-12">
        <div class="row g-4">
          <div class="col-lg">
            <div class="card h-100">
              <h1 class="card-header d-flex align-items-center gap-2">
                <div class="me-auto">
                  <i :class="['bi', platformIcon(platform)]"></i>
                  {{ platform.display_name }}
                  <span
                    class="text-muted d-block"
                    style="font-size: 0.5em"
                    v-if="parent"
                  >
                    Counted in
                    <a :href="'/platform/' + parent.id">{{
                      parent.display_name
                    }}</a>
                  </span>
                </div>
                <AdminEditLink tab="platforms" :id="platform.id" />
              </h1>
              <div class="card-body">
                <InfoStatTiles
                  :stats="stats"
                  :counts="[
                    { label: 'Games', value: stats.game_count },
                    { label: 'Users', value: stats.user_count },
                  ]"
                  :background="platformBackground(platform)"
                  :color="platformTextColor(platform)"
                  :combinedNote="
                    withChildren
                      ? 'Including the platforms in the breakdown'
                      : undefined
                  "
                />
              </div>
            </div>
          </div>
          <YourStatsCard
            class="col-lg-4"
            :platform="platform"
            :includeChildren="withChildren"
          />
        </div>
      </div>

      <div v-if="withChildren" class="col-12">
        <ChildPlatformsCard :platform="platform" />
      </div>

      <!-- recent activity, and what's played the most on it next to it -->
      <div class="col-lg-8">
        <RecentActivityCard
          :platform="platform"
          :includeChildPlatforms="withChildren"
          :limit="20"
        />
      </div>
      <div class="col-lg-4">
        <!-- one card, the picker applies to everything in it -->
        <div class="card">
          <h2 class="card-header">Top lists</h2>
          <div class="card-body d-flex flex-column gap-4">
            <DateRangerPicker
              storageKey="top"
              :relativeMillis="-1"
              @updated:both="
                ({ before, after }) => {
                  topBefore = before;
                  topAfter = after;
                  topReady = true;
                }
              "
            />
            <template v-if="topReady">
              <TopGamesList
                :platform="platform"
                :includeChildPlatforms="withChildren"
                :after="topAfter"
                :before="topBefore"
                :limit="10"
              />
              <TopPlayersCard
                :platform="platform"
                :includeChildPlatforms="withChildren"
                :compact="true"
                :after="topAfter"
                :before="topBefore"
                :limit="10"
              />
            </template>
          </div>
        </div>
      </div>
      <div class="col-12">
        <PlaytimeCharts
          :platform="platform"
          :includeChildPlatforms="withChildren"
        />
      </div>
    </div>
  </template>
</template>
