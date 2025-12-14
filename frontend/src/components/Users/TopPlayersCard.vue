<script setup lang="ts">
import { onMounted, ref } from "vue";
import RowV2 from "../ActivityRows/RowV2.vue";
import DateRangerPicker from "../Misc/DateRangerPicker.vue";
import type { Game, Platform, User } from "../../api.models";
import { TimeplayedAPI } from "../../api.client";
import type { UserWithStats } from "../../api.models";

const props = defineProps<{
  game?: Game;
  platform?: Platform;
  startingRelativeDays?: number;
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
    const data = await TimeplayedAPI.getUsers({
      offset: _users.value.length,
      limit: 100,
      gameId: props.game ? props.game.id : undefined,
      before: _before.value ? _before.value.getTime() : undefined,
      after: _after.value ? _after.value.getTime() : undefined,
      platformId: props.platform ? props.platform.id : undefined,
    });

    _users.value.push(...data.data);

    if (data.total === _users.value.length) {
      break;
    }
  }
  _users.value.sort((a, b) => b.totals.playtime_secs - a.totals.playtime_secs);
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
        :relative-days="7"
      />
      <table class="table table-sm table-hover table-responsive">
        <tbody v-if="!_loading">
          <RowV2
            v-for="user in _users"
            :key="user.user.id"
            :user="user"
            :duration-seconds="user.totals.playtime_secs"
            :context="props.game ? 'gamePage' : 'frontPage'"
          />
        </tbody>
      </table>
      <p v-if="!_loading && _users.length === 0" class="text-secondary">
        No one seems to have played this in the selected period
      </p>
    </div>
  </div>
</template>
