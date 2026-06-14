<script setup lang="ts">
import { onMounted, ref } from "vue";
import RowV2 from "../ActivityRows/RowV2.vue";
import DateRangerPicker from "../Misc/DateRangerPicker.vue";
import type { Game, Platform } from "../../api.models";
import { TimeplayedAPI } from "../../api.client";
import type { UserWithStats } from "../../api.models";

const ONE_HOUR = 60 * 60 * 1000;
const ONE_DAY = 24 * ONE_HOUR;

const props = defineProps<{
  game?: Game;
  platform?: Platform;
  context: "gamePage" | "frontPage" | "platformPage";
}>();

const _users = ref<UserWithStats[]>([]);
const _loading = ref(false);
const _before = ref<Date | undefined>();
const _after = ref<Date | undefined>();

async function fetchTheThings() {
  if (_loading.value) {
    return;
  }
  _loading.value = true;
  _users.value = [];
  while (true) {
    const data = await TimeplayedAPI.getUsersStats({
      offset: _users.value.length,
      limit: 100,
      game: props.game ? props.game.id : undefined,
      before: _before.value ? _before.value.getTime() : undefined,
      after: _after.value ? _after.value.getTime() : undefined,
      platform: props.platform ? props.platform.id : undefined,
      order: "desc",
      sort: "playtime",
    });
    if (data.length === 0 || data.length < 100) {
      break;
    }
    _users.value.push(...data);
  }
  _loading.value = false;
}

onMounted(() => {});
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
        :relative-millis="context === 'frontPage' ? 7 * ONE_DAY : -1"
        :toggleable="context !== 'frontPage'"
      />
      <table
        class="table table-sm table-hover table-responsive"
        v-if="_users.length > 0"
      >
        <thead>
          <tr>
            <th></th>
            <th>User</th>
            <th>Time played</th>
            <th
              v-if="props.context !== 'frontPage' && _after === undefined"
              class="d-none d-md-table-cell"
            >
              Last played
            </th>
          </tr>
        </thead>

        <tbody v-if="!_loading">
          <RowV2
            v-for="user in _users"
            :key="user.id"
            :user="user"
            :duration-seconds="user.stats.seconds"
            :context="props.context"
            :show-users="false"
            :show-date="props.context !== 'frontPage' && _after === undefined"
            :date="
              user.stats.last_activity
                ? new Date(user.stats.last_activity)
                : undefined
            "
          />
        </tbody>
      </table>
      <p v-if="!_loading && _users.length === 0" class="text-muted text-center">
        Nothing found
      </p>
    </div>
  </div>
</template>
