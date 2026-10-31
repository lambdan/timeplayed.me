<script setup lang="ts">
import { computed, ref, watch } from "vue";
import DateRangerPicker from "../Misc/DateRangerPicker.vue";
import DiscordAvatar from "../DiscordAvatar.vue";
import CalendarBasic from "../CalendarBasic.vue";
import { formatDuration } from "../../utils";
import type { Game, Platform } from "../../api.models";
import { TimeplayedAPI } from "../../api.client";
import type { UserWithStats } from "../../api.models";

const props = defineProps<{
  game?: Game;
  platform?: Platform;
  /** ranked list without a date picker, the range comes from after/before */
  compact?: boolean;
  after?: Date;
  before?: Date;
  /** only show the top x */
  limit?: number;
  /** only users with names matching this */
  search?: string;
}>();

const _users = ref<UserWithStats[]>([]);
const _loading = ref(false);
const _before = ref<Date | undefined>();
const _after = ref<Date | undefined>();
// to ignore answers from older requests, declared before the watch below runs
let latest = 0;

const shown = computed(() =>
  props.limit ? _users.value.slice(0, props.limit) : _users.value,
);

// in compact mode the range comes from the page instead of our own picker
watch(
  () => [props.compact, props.search, props.after, props.before],
  () => {
    if (!props.compact) return;
    _after.value = props.after;
    _before.value = props.before;
    fetchTheThings();
  },
  { immediate: true },
);

async function fetchTheThings() {
  // TODO: Change this to show more system (like game table)
  const request = ++latest;
  _loading.value = true;
  _users.value = [];
  let offset = 0;
  while (true) {
    const data = await TimeplayedAPI.getUsersStats({
      offset,
      limit: 100,
      game: props.game ? props.game.id : undefined,
      before: _before.value ? _before.value.getTime() : undefined,
      after: _after.value ? _after.value.getTime() : undefined,
      platform: props.platform ? props.platform.id : undefined,
      search: props.search || undefined,
      order: "desc",
      sort: "playtime",
    });
    if (request !== latest) return; // a newer range was picked meanwhile
    for (const u of data) {
      offset += 1;
      // only include users with playtime
      if (u.stats.seconds > 0) {
        _users.value.push(u);
      }
    }
    if (data.length === 0 || data.length < 100) {
      break;
    }
  }
  _loading.value = false;
}

// last played is useful on platform pages, and only makes sense for all time. no room for it in the compact list
const showLastPlayed = computed(
  () => !props.compact && !!props.platform && _after.value === undefined,
);
</script>

<template>
  <!-- compact = a section in a bigger card (front page), so no card of its own -->
  <div :class="{ 'card p-0': !compact }">
    <h2 v-if="!compact" class="card-header">Top players</h2>
    <h3 v-else class="h5 mb-2">Players</h3>
    <div :class="{ 'card-body': !compact }">
      <DateRangerPicker
        v-if="!compact"
        class="mb-2"
        @updated:both="
          ({ before, after }) => {
            _before = before;
            _after = after;
            fetchTheThings();
          }
        "
        :relative-millis="-1"
        :toggleable="true"
      />
      <table
        class="table table-sm table-hover table-responsive"
        v-if="_users.length > 0"
      >
        <!-- compact version is a plain ranked list like TopGamesList -->
        <thead v-if="!compact">
          <tr>
            <th></th>
            <th>User</th>
            <th>Playtime</th>
            <th v-if="showLastPlayed" class="d-none d-md-table-cell">
              Last played
            </th>
          </tr>
        </thead>

        <tbody v-if="!_loading" class="align-middle">
          <tr v-for="(user, i) in shown" :key="user.id">
            <td v-if="compact" class="text-body-secondary" style="width: 1%">
              {{ i + 1 }}
            </td>
            <td style="width: 50px">
              <DiscordAvatar :user="user" :maxWidth="40" />
            </td>
            <td class="text-break">
              <a
                :href="`/user/${user.id}`"
                class="link-underline link-underline-opacity-0"
                >{{ user.display_name }}</a
              >
            </td>
            <td class="text-nowrap" :class="{ 'text-end': compact }">
              {{ formatDuration(user.stats.seconds) }}
            </td>
            <td
              v-if="showLastPlayed"
              class="text-nowrap d-none d-md-table-cell"
            >
              <CalendarBasic :date="user.stats.last_activity" />
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!_loading && _users.length === 0" class="text-muted text-center">
        {{ search ? "No matches" : "Nothing found" }}
      </p>
    </div>
  </div>
</template>
