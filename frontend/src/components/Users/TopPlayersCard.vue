<script setup lang="ts">
import { onMounted, ref } from "vue";
import { fetchUsers } from "../../utils";
import RowV2 from "../ActivityRows/RowV2.vue";
import DateRangerPicker from "../Misc/DateRangerPicker.vue";
import type { Game, User } from "../../api.models";

const props = defineProps<{
  game?: Game;
  startingRelativeDays?: number;
}>();

const _users = ref<
  { user: User; duration: number; count: number; last_played: Date }[]
>([]);
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
    const res = await fetchUsers({
      offset: _users.value.length,
      limit: 100,
      gameId: props.game ? props.game.id : undefined,
      before: _before.value,
      after: _after.value,
    });

    for (const u of res.data) {
      _users.value.push({
        user: u.user,
        duration: u.totals.playtime_secs,
        count: u.totals.activity_count,
        last_played: new Date(u.newest_activity.timestamp),
      });
    }

    if (res.total === _users.value.length) {
      break;
    }
  }
  _users.value.sort((a, b) => b.duration - a.duration);
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
            :user="user.user"
            :duration-seconds="user.duration"
            :context="props.game ? 'gamePage' : 'frontPage'"
          />
        </tbody>
      </table>
      <p v-if ="!_loading && _users.length === 0" class="text-secondary">No one seems to have played this in the selected period</p>
    </div>
  </div>
</template>
