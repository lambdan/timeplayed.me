<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  AdminAPI,
  type AdminLiveActivity,
  type AdminPresence,
  type AdminTrackedPresence,
} from "../../admin.client";
import { TimeplayedAPI } from "../../api.client";
import { formatDate, timeAgo } from "../../utils";
import DurationBadge from "../Badges/DurationBadge.vue";

// same as STALE_AFTER in backend/tpbackend/discord/presence.py
const STALE_AFTER_MS = 5 * 60 * 1000;

const live = ref<AdminLiveActivity[]>();
const presence = ref<AdminPresence>();
const error = ref("");
const loading = ref(false);
// when it was fetched, so durations and "ago" are up to then
const fetched = ref(0);

// discard needs a second click
const discardArmed = ref<number>();

async function discard(id: number) {
  if (discardArmed.value !== id) {
    discardArmed.value = id;
    return;
  }
  discardArmed.value = undefined;
  try {
    error.value = "";
    await AdminAPI.discardLiveActivity(id);
    live.value = live.value?.filter((l) => l.id !== id);
  } catch (e: any) {
    error.value = e.message;
  }
}

const trackedCount = computed(
  () => presence.value?.members.reduce((n, m) => n + m.tracked.length, 0) ?? 0,
);

async function load() {
  loading.value = true;
  try {
    error.value = "";
    [live.value, presence.value] = await Promise.all([
      AdminAPI.getLiveActivities(),
      AdminAPI.getPresence(),
    ]);
    fetched.value = Date.now();
  } catch (e: any) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

// how long the session is if it ends now, like close() in presence.py
function seconds(tracked: AdminTrackedPresence) {
  const start = Math.min(
    tracked.started,
    tracked.discord_started ?? tracked.started,
  );
  return Math.round((fetched.value - start) / 1000);
}

// not seen for so long the bot wasn't watching, it closes at last seen
function stale(tracked: AdminTrackedPresence) {
  return fetched.value - tracked.last_seen > STALE_AFTER_MS;
}

onMounted(load);
</script>

<template>
  <div>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div class="d-flex align-items-center mb-2">
      <h5 class="mb-0 me-auto">Manual tracking</h5>
      <button
        class="btn btn-outline-primary btn-sm"
        :disabled="loading"
        @click="load"
      >
        <i class="bi bi-arrow-clockwise"></i> Refresh
      </button>
    </div>
    <template v-if="live">
      <div v-if="live.length === 0" class="text-body-secondary mb-4">
        Nobody is tracking manually
      </div>
      <div v-else class="table-responsive mb-4">
        <table class="table table-sm align-middle">
          <thead>
            <tr>
              <th>User</th>
              <th>Game</th>
              <th>Platform</th>
              <th class="d-none d-md-table-cell">Started</th>
              <th>Duration</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="l in live" :key="l.id">
              <td class="text-nowrap">
                <a :href="`/admin?tab=users&id=${l.user_id}`">{{
                  l.user_name
                }}</a>
                <span
                  v-if="!l.manual_activity"
                  class="badge text-bg-warning ms-1"
                  title="Without manual_activity they can't stop it"
                  >No manual_activity</span
                >
              </td>
              <td>
                <a :href="`/admin?tab=games&id=${l.game_id}`">{{
                  l.game_name
                }}</a>
              </td>
              <td>{{ l.platform_abbreviation }}</td>
              <td class="text-nowrap d-none d-md-table-cell">
                {{ formatDate(l.started) }}
              </td>
              <td>
                <DurationBadge
                  :seconds="Math.round((fetched - l.started) / 1000)"
                />
              </td>
              <td class="text-end text-nowrap">
                <button
                  class="btn btn-sm"
                  :class="
                    discardArmed === l.id ? 'btn-danger' : 'btn-outline-danger'
                  "
                  title="Discard: removes it without storing an activity"
                  aria-label="Discard"
                  @click="discard(l.id)"
                >
                  <i class="bi bi-stop-fill"></i>
                  {{ discardArmed === l.id ? "Really discard?" : "" }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <h5>Discord presence</h5>
    <p class="text-body-secondary small">
      Everyone the bot sees playing something, and the sessions it tracks.
      Presences are checked every minute and on every change. Every "playing"
      activity is tracked, also when someone has several at the same time.
    </p>

    <div class="d-flex flex-wrap align-items-center gap-2 mb-3">
      <template v-if="presence">
        <span
          class="badge"
          :class="presence.connected ? 'text-bg-success' : 'text-bg-danger'"
          >{{
            presence.connected ? "Bot connected" : "Bot not connected"
          }}</span
        >
        <span
          class="small"
          :title="
            presence.last_checked ? formatDate(presence.last_checked) : ''
          "
          >Last check:
          {{
            presence.last_checked ? timeAgo(presence.last_checked) : "never"
          }}</span
        >
        <span class="small">{{ trackedCount }} tracked</span>
      </template>
    </div>

    <template v-if="presence">
      <div v-if="presence.members.length === 0" class="text-body-secondary">
        Nobody is playing
      </div>
      <ul v-else class="list-group">
        <li
          v-for="m in presence.members"
          :key="m.discord_user_id"
          class="list-group-item"
        >
          <div class="d-flex flex-wrap align-items-center gap-2">
            <img
              :src="TimeplayedAPI.getDiscordAvatarUrl(m.discord_user_id)"
              class="rounded-circle"
              width="24"
              height="24"
            />
            <strong>{{ m.discord_user_name }}</strong>
            <a
              v-if="m.user_id"
              class="small"
              :href="`/admin?tab=users&id=${m.user_id}`"
              >user #{{ m.user_id }}</a
            >
            <span v-else class="small text-body-secondary">no user yet</span>
            <span v-if="!m.synced" class="badge text-bg-warning"
              >Not stored (no discord_tracking)</span
            >
          </div>

          <div
            v-for="t in m.tracked"
            :key="`${t.game_name}|${t.platform}`"
            class="small mt-1"
          >
            <div class="d-flex flex-wrap align-items-center gap-2">
              <span>
                Tracking <strong>{{ t.game_name }}</strong> ({{ t.platform }})
              </span>
              <DurationBadge :seconds="seconds(t)" />
              <span v-if="stale(t)" class="badge text-bg-warning"
                >Stale, ends at last seen</span
              >
            </div>
            <div class="text-body-secondary">
              First seen {{ formatDate(t.started) }}, Discord start
              {{ t.discord_started ? formatDate(t.discord_started) : "-" }},
              last seen
              <span :title="formatDate(t.last_seen)">{{
                timeAgo(t.last_seen)
              }}</span>
            </div>
          </div>
          <div
            v-if="m.tracked.length === 0"
            class="small mt-1 text-warning-emphasis"
          >
            Not tracked
          </div>

          <ul v-if="m.activities.length" class="small mb-0 mt-1 ps-3">
            <li v-for="(a, i) in m.activities" :key="i">
              {{ a.type }}: {{ a.name ?? "-" }}
              <template v-if="a.platform">({{ a.platform }})</template>
              <span v-if="a.details" class="text-body-secondary">
                · {{ a.details }}</span
              >
              <span v-if="a.state" class="text-body-secondary">
                · {{ a.state }}</span
              >
              <span v-if="a.start" class="text-body-secondary">
                · started {{ formatDate(a.start) }}</span
              >
            </li>
          </ul>
          <div v-else class="small mt-1 text-body-secondary">
            Not seen in any server
          </div>
        </li>
      </ul>
    </template>
  </div>
</template>
