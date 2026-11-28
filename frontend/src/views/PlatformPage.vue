<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import type { Platform, PlatformWithStats } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import AdminEditLink from "../components/Misc/AdminEditLink.vue";
import PlatformBadge from "../components/Badges/PlatformBadge.vue";
import PlatformMetadataCard from "../components/Platforms/PlatformMetadataCard.vue";
import YourStatsCard from "../components/Users/YourStatsCard.vue";
import TopGamesList from "../components/Games/TopGamesList.vue";
import TopPlayersCard from "../components/Users/TopPlayersCard.vue";
import RecentActivityCard from "../components/RecentActivityCard.vue";
import DateRangerPicker from "../components/Misc/DateRangerPicker.vue";
import PlaytimeCharts from "../components/Charts/PlaytimeCharts.vue";
import CalendarBasic from "../components/CalendarBasic.vue";
import ChildPlatformsCard from "../components/Platforms/ChildPlatformsCard.vue";
import { formatDuration } from "../utils";
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
      <div class="col-lg-8">
        <div class="card h-100">
          <h1 class="card-header d-flex align-items-center gap-2">
            <div class="me-auto">
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
            <div class="row g-3">
              <div class="col-12 col-sm-auto text-center">
                <PlatformBadge :platform="platform" class="fs-4" />
              </div>
              <div class="col">
                <table class="table table-sm table-hover mb-0">
                  <tbody>
                    <tr>
                      <th class="text-nowrap">Playtime</th>
                      <td>
                        {{ formatDuration(stats.seconds) }}
                        <span
                          v-if="withChildren"
                          class="text-muted"
                          title="Combined total"
                          >*</span
                        >
                      </td>
                    </tr>
                    <tr>
                      <th class="text-nowrap">Activities</th>
                      <td>
                        {{ stats.activity_count }}
                        <span
                          v-if="withChildren"
                          class="text-muted"
                          title="Combined total"
                          >*</span
                        >
                      </td>
                    </tr>
                    <tr>
                      <th class="text-nowrap">Games</th>
                      <td>
                        {{ stats.game_count }}
                        <span
                          v-if="withChildren"
                          class="text-muted"
                          title="Combined total"
                          >*</span
                        >
                      </td>
                    </tr>
                    <tr>
                      <th class="text-nowrap">Users</th>
                      <td>
                        {{ stats.user_count }}
                        <span
                          v-if="withChildren"
                          class="text-muted"
                          title="Combined total"
                          >*</span
                        >
                      </td>
                    </tr>
                    <tr v-if="stats.first_activity">
                      <th class="text-nowrap">First played</th>
                      <td>
                        <CalendarBasic
                          :date="stats.first_activity"
                          :showIcon="false"
                          :absolute="true"
                        />
                      </td>
                    </tr>
                    <tr v-if="stats.last_activity">
                      <th class="text-nowrap">Last played</th>
                      <td>
                        <CalendarBasic
                          :date="stats.last_activity"
                          :showIcon="false"
                          :absolute="true"
                        />
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-lg-4 d-flex flex-column gap-4">
        <YourStatsCard :platform="platform" :includeChildren="withChildren" />
        <PlatformMetadataCard class="flex-grow-1" :platform="platform" />
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
