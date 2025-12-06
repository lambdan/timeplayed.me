<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { Activity, Game, User } from "../models/models";
import UserPageActivityRow from "./ActivityRows/UserPageActivityRow.vue";
import FrontPageActivityRow from "./ActivityRows/FrontPageActivityRow.vue";
import GamePageActivityRow from "./ActivityRows/GamePageActivityRow.vue";
import { fetchActivities as FU } from "../utils";

const props = withDefaults(
  defineProps<{
    user?: User;
    game?: Game;
    limit: number;
    showExpand?: boolean;
  }>(),
  {
    showExpand: false,
    limit: 25,
    user: undefined,
    game: undefined,
  }
);

const activities = ref<Activity[]>([]);
const offset = ref(0);
const loading = ref(false);
const hasMore = ref(true);

async function fetchActivities(limit?: number, offsetVal = 0) {
  const data = await FU({
    limit,
    offset: offsetVal,
    game: props.game ? props.game.id : undefined,
    user: props.user ? props.user.id : undefined
  });
  const newActivities = data.data.map((activity: any) => ({
    ...activity,
    createdAt: new Date(activity.timestamp),
  }));

  if (offsetVal === 0) {
    activities.value = newActivities;
  } else {
    activities.value = [...activities.value, ...newActivities];
  }

  hasMore.value = data._total > offsetVal + newActivities.length;
  loading.value = false;
}

function loadMore() {
  offset.value += props.limit;
  fetchActivities(props.limit, offset.value);
}

onMounted(() => {
  fetchActivities(props.limit, 0);
});
</script>

<template>
  <div class="card p-0">
    <h2 class="card-header">Activity</h2>
    <div class="card-body">
      <FrontPageActivityRow
        v-if="!props.user && !props.game"
        v-for="activity in activities"
        :key="activity.id"
        :activity="activity"
        :showExpand="showExpand"
      />
      <UserPageActivityRow
        v-if="props.user && !props.game"
        v-for="activity in activities"
        :key="activity.id"
        :activity="activity"
        :showExpand="showExpand"
      />
      <GamePageActivityRow
        v-if="props.game && !props.user"
        v-for="activity in activities"
        :key="activity.id"
        :activity="activity"
        :showExpand="showExpand"
      />

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
      </div>
    </div>
  </div>
</template>
