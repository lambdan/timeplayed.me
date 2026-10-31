<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import UserInfoCard from "../components/UserInfoCard.vue";
import RecentActivityCard from "../components/RecentActivityCard.vue";
import TopGamesList from "../components/Games/TopGamesList.vue";
import TopPlatformsList from "../components/Platforms/TopPlatformsList.vue";
import DateRangerPicker from "../components/Misc/DateRangerPicker.vue";
import PlaytimeCharts from "../components/Charts/PlaytimeCharts.vue";
import type { UserWithStats } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import { updateDocumentTitle } from "../utils";

const route = useRoute();
const user = ref<UserWithStats>();
// date range for the top lists next to recent activity, set by their picker
const topAfter = ref<Date>();
const topBefore = ref<Date>();
// lists wait for the pickers first range
const topReady = ref(false);

onMounted(async () => {
  const userId = parseInt(route.params.id as string);
  user.value = await TimeplayedAPI.getUserStats(userId);
  updateDocumentTitle(user.value.display_name);
});
</script>

<template>
  <div v-if="!user" class="text-center mt-4">
    <div class="spinner-border" role="status"></div>
  </div>

  <template v-else>
    <div class="row">
      <div class="col-12 p-0 mt-4">
        <UserInfoCard :user="user" />
      </div>
    </div>

    <!-- recent activity, and what they played the most next to it -->
    <div class="row mt-4">
      <div class="col-lg-8 p-0 pe-lg-4">
        <RecentActivityCard :user="user" :limit="12" />
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
                :user="user"
                :after="topAfter"
                :before="topBefore"
                :limit="10"
              />
              <TopPlatformsList
                :user="user"
                :after="topAfter"
                :before="topBefore"
                :limit="10"
              />
            </template>
          </div>
        </div>
      </div>
    </div>

    <PlaytimeCharts class="mb-4" :user="user" />
  </template>
</template>
