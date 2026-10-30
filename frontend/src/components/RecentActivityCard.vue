<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import type { Activity, Game, Platform, User } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import { formatDuration } from "../utils";
import { heatBadgeStyle } from "../utils.heat";
import DateRangerPicker from "./Misc/DateRangerPicker.vue";
import DiscordAvatar from "./DiscordAvatar.vue";
import CroppedCover from "./Games/CroppedCover.vue";
import PlatformBadge from "./Badges/PlatformBadge.vue";
import CalendarBasic from "./CalendarBasic.vue";

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
    user: undefined,
    game: undefined,
  },
);

const fetching = ref(false);
const FAKE_SLEEP = 500;

const activities = ref<Activity[]>([]);
const loading = ref(false);
const hasMore = ref(true);

const _before = ref<Date | undefined>();
const _after = ref<Date | undefined>();

const total = ref(0);
const seen = ref(new Set<number>());

// what the rows show, the api calls are cached so this is cheap
const users = reactive(new Map<number, User>());
const games = reactive(new Map<number, Game>());
const platforms = reactive(new Map<number, Platform>());

// so the same id isn't fetched once per row before the first answer is cached
const requested = new Set<string>();

function lookup(list: Activity[]) {
  const once = (key: string, fetch: () => void) => {
    if (requested.has(key)) return;
    requested.add(key);
    fetch();
  };
  for (const a of list) {
    if (!props.user) {
      once(`u${a.user_id}`, () =>
        TimeplayedAPI.getUser(a.user_id).then((u) => users.set(u.id, u)),
      );
    }
    if (!props.game) {
      once(`g${a.game_id}`, () =>
        TimeplayedAPI.getGame(a.game_id).then((g) => games.set(g.id, g)),
      );
    }
    once(`p${a.platform_id}`, () =>
      TimeplayedAPI.getPlatform(a.platform_id).then((p) =>
        platforms.set(p.id, p),
      ),
    );
  }
}

async function fetchActivities(limit?: number) {
  loading.value = true;
  fetching.value = true;
  const data = await TimeplayedAPI.getActivities({
    limit,
    offset: activities.value.length,
    game: props.game ? props.game.id : undefined,
    user: props.user ? props.user.id : undefined,
    before: _before.value ? _before.value.getTime() : Date.now(),
    after: _after.value ? _after.value.getTime() : undefined,
  });

  const newActivities = data.map((activity: any) => ({
    ...activity,
    createdAt: new Date(activity.timestamp),
  }));
  activities.value.push(...newActivities);
  lookup(newActivities);
  loading.value = false;
  sortByRecent();

  await new Promise((resolve) => setTimeout(resolve, FAKE_SLEEP));
  fetching.value = false;
}

async function autoRefresh() {
  for (const a of activities.value) {
    seen.value.add(a.id);
  }
  let lastCheck = Date.now();
  while (true) {
    await new Promise((resolve) => setTimeout(resolve, 5000));
    fetching.value = true;
    const data = await TimeplayedAPI.getActivities({
      offset: 0,
      game: props.game ? props.game.id : undefined,
      user: props.user ? props.user.id : undefined,
      after: lastCheck,
      order: "desc",
    });
    for (const activity of data) {
      if (seen.value.has(activity.id)) {
        continue;
      }
      activities.value.unshift({
        ...activity,
      });
      lookup([activity]);
      seen.value.add(activity.id);
    }
    total.value += data.length;
    lastCheck = Date.now();
    sortByRecent();
    await new Promise((resolve) => setTimeout(resolve, FAKE_SLEEP));
    fetching.value = false;
  }
}

function sortByRecent() {
  activities.value.sort((a, b) => b.timestamp - a.timestamp);
}

function loadMore() {
  fetchActivities();
}

onMounted(async () => {
  await fetchActivities(props.limit);
  autoRefresh();
});
</script>

<template>
  <div class="card p-0">
    <h2 class="card-header">
      Recent activity

      <span
        v-if="fetching"
        class="spinner-border spinner-border-sm float-end mt-3"
        role="status"
        aria-hidden="true"
      ></span>
    </h2>
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

      <!-- columns that would just repeat the page (like the game on a game page) are left out -->
      <table class="table table-sm table-hover table-responsive align-middle">
        <tbody>
          <tr v-for="a in activities" :key="a.id">
            <td v-if="!user" style="width: 50px">
              <DiscordAvatar
                v-if="users.get(a.user_id)"
                :user="users.get(a.user_id)!"
                :maxWidth="40"
              />
            </td>
            <td v-if="!game" class="d-none d-md-table-cell" style="width: 50px">
              <CroppedCover
                :gameId="a.game_id"
                :thumb="true"
                style="width: 32px"
              />
            </td>
            <td v-if="!game" class="w-100 text-break">
              <a
                :href="`/game/${a.game_id}`"
                class="link-underline link-underline-opacity-0"
                >{{ games.get(a.game_id)?.name }}</a
              >
            </td>
            <!-- width 1% = only as wide as the content, so these stay together at the end -->
            <td class="d-none d-md-table-cell" style="width: 1%">
              <PlatformBadge
                v-if="platforms.get(a.platform_id)"
                :platform="platforms.get(a.platform_id)!"
                :showName="false"
              />
            </td>
            <td class="text-nowrap px-md-3" style="width: 1%">
              <!-- colored by length, same scale as the recap heatmap -->
              <a
                :href="`/activity/${a.id}`"
                class="badge fw-semibold text-decoration-none"
                :style="{
                  ...heatBadgeStyle(a.seconds),
                  fontVariantNumeric: 'tabular-nums',
                }"
                :title="`${a.seconds} seconds`"
                >{{ formatDuration(a.seconds, true) }}</a
              >
            </td>
            <td class="text-nowrap" style="width: 1%">
              <!-- shorter on phones -->
              <CalendarBasic
                class="d-none d-md-inline"
                :date="new Date(a.timestamp)"
              />
              <CalendarBasic
                class="d-md-none"
                :date="new Date(a.timestamp)"
                :short="true"
                :showIcon="false"
              />
            </td>
          </tr>
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
          {{ activities.length }} activities loaded
        </small>
      </div>
    </div>
  </div>
</template>
