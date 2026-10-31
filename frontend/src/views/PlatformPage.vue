<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import type { PlatformWithStats } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import PlatformBadge from "../components/Badges/PlatformBadge.vue";
import PlatformMetadataCard from "../components/Platforms/PlatformMetadataCard.vue";
import TopGamesList from "../components/Games/TopGamesList.vue";
import TopPlayersCard from "../components/Users/TopPlayersCard.vue";
import RecentActivityCard from "../components/RecentActivityCard.vue";
import DateRangerPicker from "../components/Misc/DateRangerPicker.vue";
import PlaytimeCharts from "../components/Charts/PlaytimeCharts.vue";
import CalendarBasic from "../components/CalendarBasic.vue";
import { formatDuration, updateDocumentTitle } from "../utils";

const route = useRoute();
const platform = ref<PlatformWithStats>();
// date range for the top lists next to recent activity, set by their picker
const topAfter = ref<Date>();
const topBefore = ref<Date>();
// lists wait for the pickers first range
const topReady = ref(false);

onMounted(async () => {
  const platformId = parseInt(route.params.id as string);
  platform.value = await TimeplayedAPI.getPlatformStats(platformId);
  updateDocumentTitle(platform.value.display_name);
});
</script>

<template>
  <div v-if="!platform" class="text-center mt-4">
    <div class="spinner-border" role="status"></div>
  </div>

  <template v-else>
    <div class="row">
      <div class="col-lg-8 p-0 pe-lg-4 mt-4">
        <div class="card p-0 h-100">
          <h1 class="card-header">{{ platform.display_name }}</h1>
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
                      <td>{{ formatDuration(platform.stats.seconds) }}</td>
                    </tr>
                    <tr>
                      <th class="text-nowrap">Activities</th>
                      <td>{{ platform.stats.activity_count }}</td>
                    </tr>
                    <tr>
                      <th class="text-nowrap">Games</th>
                      <td>{{ platform.stats.game_count }}</td>
                    </tr>
                    <tr>
                      <th class="text-nowrap">Users</th>
                      <td>{{ platform.stats.user_count }}</td>
                    </tr>
                    <tr v-if="platform.stats.first_activity">
                      <th class="text-nowrap">First played</th>
                      <td>
                        <CalendarBasic
                          :date="platform.stats.first_activity"
                          :showIcon="false"
                          :absolute="true"
                        />
                      </td>
                    </tr>
                    <tr v-if="platform.stats.last_activity">
                      <th class="text-nowrap">Last played</th>
                      <td>
                        <CalendarBasic
                          :date="platform.stats.last_activity"
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
      <div class="col-lg-4 p-0 mt-4">
        <PlatformMetadataCard class="h-100" :platform="platform" />
      </div>
    </div>

    <!-- recent activity, and what's played the most on it next to it -->
    <div class="row mt-4">
      <div class="col-lg-8 p-0 pe-lg-4">
        <RecentActivityCard :platform="platform" :limit="20" />
      </div>
      <div class="col-lg-4 p-0 mt-4 mt-lg-0">
        <!-- one card, the picker applies to everything in it -->
        <div class="card p-0">
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
                :after="topAfter"
                :before="topBefore"
                :limit="10"
              />
              <TopPlayersCard
                :platform="platform"
                :compact="true"
                :after="topAfter"
                :before="topBefore"
                :limit="10"
              />
            </template>
          </div>
        </div>
      </div>
    </div>

    <PlaytimeCharts class="mb-4" :platform="platform" />
  </template>
</template>
