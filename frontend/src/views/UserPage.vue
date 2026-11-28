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
import { usePageTitle } from "../composables/usePageTitle";
import { themeColor } from "../pageTheme";
import { usePageColors } from "../composables/usePageColors";

const route = useRoute();
const setTitle = usePageTitle();
const user = ref<UserWithStats>();
// also private users, to everyone but themselves
const notFound = ref(false);
// date range for the top lists next to recent activity, set by their picker
const topAfter = ref<Date>();
const topBefore = ref<Date>();
// lists wait for the pickers first range
const topReady = ref(false);
// the user's colors, the default page if they have none
usePageColors(() => {
  if (notFound.value) return null;
  if (!user.value) return undefined;
  if (!user.value.color_primary) return null;
  return {
    primary: themeColor(user.value.color_primary),
    secondary: themeColor(user.value.color_secondary),
  };
});

onMounted(async () => {
  const userId = parseInt(route.params.id as string);
  try {
    user.value = await TimeplayedAPI.getUserStats(userId);
  } catch {
    notFound.value = true;
    return;
  }
  setTitle(`${user.value.display_name} playtime`);
});
</script>

<template>
  <p v-if="notFound" class="text-center">User not found</p>
  <div v-else-if="!user" class="text-center">
    <div class="spinner-border" role="status"></div>
  </div>

  <template v-else>
    <div class="row g-4">
      <div class="col-12">
        <UserInfoCard :user="user" />
      </div>

      <!-- recent activity, and what they played the most next to it -->
      <div class="col-lg-8">
        <RecentActivityCard :user="user" :limit="12" />
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
      <div class="col-12">
        <PlaytimeCharts :user="user" />
      </div>
    </div>
  </template>
</template>
