<script setup lang="ts">
import { computed, ref } from "vue";
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
}>();

const _users = ref<UserWithStats[]>([]);
const _loading = ref(false);
const _before = ref<Date | undefined>();
const _after = ref<Date | undefined>();

async function fetchTheThings() {
  // TODO: Change this to show more system (like game table)
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
      order: "desc",
      sort: "playtime",
    });
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

// last played is useful on platform pages, and only makes sense for all time
const showLastPlayed = computed(
  () => !!props.platform && _after.value === undefined,
);
</script>

<template>
  <div class="card p-0">
    <h2 class="card-header">Top players</h2>
    <div class="card-body">
      <DateRangerPicker
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
        <thead>
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
          <tr v-for="user in _users" :key="user.id">
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
            <td class="text-nowrap">
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
        Nothing found
      </p>
    </div>
  </div>
</template>
