<script setup lang="ts">
import { onMounted, ref } from "vue";
import RowV2 from "./ActivityRows/RowV2.vue";
import type { Activity, Game, User } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import DateRangerPicker from "./Misc/DateRangerPicker.vue";

const props = withDefaults(
  defineProps<{
    user?: User;
    game?: Game;
    limit?: number;
    showExpand?: boolean;
    showDateRange?: boolean;
  }>(),
  {
    showExpand: false,
    limit: 25,
    user: undefined,
    game: undefined,
  },
);

const activities = ref<Activity[]>([]);
const loading = ref(false);
const hasMore = ref(true);

const _before = ref<Date | undefined>();
const _after = ref<Date | undefined>();

const total = ref(0);

async function fetchActivities(limit: number) {
  loading.value = true;

  const data = await TimeplayedAPI.getActivities({
    limit,
    offset: activities.value.length,
    game: props.game ? props.game.id : undefined,
    user: props.user ? props.user.id : undefined,
    before: _before.value ? _before.value.getTime() : undefined,
    after: _after.value ? _after.value.getTime() : undefined,
  });

  const newActivities = data.data.map((activity: any) => ({
    ...activity,
    createdAt: new Date(activity.timestamp),
  }));

  activities.value.push(...newActivities);

  total.value = data.total;
  hasMore.value = data.total > activities.value.length;
  loading.value = false;
}

function loadMore() {
  fetchActivities(100);
}

function getContext(): "userPage" | "gamePage" | "frontPage" {
  if (props.user && !props.game) {
    return "userPage";
  } else if (props.game && !props.user) {
    return "gamePage";
  } else {
    return "frontPage";
  }
}

onMounted(() => {
  fetchActivities(props.limit);
});
</script>

<template>
  <div class="card p-0">
    <h2 class="card-header">Activity</h2>
    <div class="card-body">
      <DateRangerPicker
        v-if="props.showDateRange"
        class="mb-2"
        @updated:both="
          ({ before, after }) => {
            _before = before;
            _after = after;
            activities.length = 0;
            fetchActivities(props.limit);
          }
        "
        :relative-days="7"
      />

      <table class="table table-sm table-hover table-responsive">
        <tbody>
          <RowV2
            v-for="activity in activities"
            :key="activity.id"
            :activity="activity"
            :context="getContext()"
            :duration-seconds="activity.seconds"
            :date="new Date(activity.timestamp)"
            :show-date="true"
            :show-users="false"
          />
        </tbody>
      </table>

      <div class="text-center my-2">
        <button v-if="loading" class="btn btn-primary" type="button" disabled>
          <span
            class="spinner-grow spinner-grow-sm"
            role="status"
            aria-hidden="true"
          ></span>
          Loading...
        </button>
        <button
          v-else-if="hasMore"
          class="btn btn-primary"
          :disabled="loading"
          @click="loadMore"
        >
          Load More
        </button>
        <br />
        <small class="text-muted mt-2">
          {{ activities.length }} / {{ total }}
        </small>
      </div>
    </div>
  </div>
</template>
