<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  AdminAPI,
  type AdminActivityDetails,
  type AdminActivityPatch,
} from "../../admin.client";
import { TimeplayedAPI } from "../../api.client";
import type { Platform } from "../../api.models";
import { formatDate, formatDuration } from "../../utils";
import AdminHistory from "./AdminHistory.vue";
import AdminSectionTabs from "./AdminSectionTabs.vue";
import AdminUnsaved from "./AdminUnsaved.vue";
import { useUnsavedChanges } from "../../composables/useUnsavedChanges";
import { unsavedFieldLabels } from "../../utils.admin";

const props = defineProps<{ activityId: number }>();
const emit = defineEmits<{ close: []; changed: []; deleted: [] }>();

const activity = ref<AdminActivityDetails>();
const platforms = ref<Platform[]>([]);
const error = ref("");
const message = ref("");
const deleteArmed = ref(false);
const section = ref("details");

const form = ref({
  game_id: "",
  user_id: "",
  platform_id: 0,
  duration: "",
  ended: "",
  hidden: false,
});

/** ms timestamp -> value for a datetime-local input (local time) */
function toLocalInput(ts: number): string {
  const offset = new Date(ts).getTimezoneOffset() * 60 * 1000;
  return new Date(ts - offset).toISOString().slice(0, 19);
}

/** "HH:MM:SS" (or "MM:SS", or just seconds) -> seconds */
function parseDuration(s: string): number {
  return s
    .split(":")
    .map((part) => parseInt(part) || 0)
    .reduce((total, part) => total * 60 + part, 0);
}

function setActivity(a: AdminActivityDetails) {
  activity.value = a;
  form.value = {
    game_id: a.game_id.toString(),
    user_id: a.user_id.toString(),
    platform_id: a.platform_id,
    duration: formatDuration(a.seconds, true),
    ended: toLocalInput(a.ended),
    hidden: a.hidden,
  };
}

/** fields in the form that differ from the saved activity, this is what save sends */
const patch = computed(() => {
  const changed: AdminActivityPatch = {};
  const a = activity.value;
  if (!a) return changed;
  const gameId = parseInt(form.value.game_id);
  if (gameId !== a.game_id) changed.game_id = gameId;
  const userId = parseInt(form.value.user_id);
  if (userId !== a.user_id) changed.user_id = userId;
  if (form.value.platform_id !== a.platform_id)
    changed.platform_id = form.value.platform_id;
  const seconds = parseDuration(form.value.duration);
  if (seconds !== a.seconds) changed.seconds = seconds;
  const ended = new Date(form.value.ended).getTime();
  // the input has no milliseconds
  if (Math.floor(ended / 1000) !== Math.floor(a.ended / 1000))
    changed.ended = ended;
  if (form.value.hidden !== a.hidden) changed.hidden = form.value.hidden;
  return changed;
});

const FIELD_LABELS: Record<keyof AdminActivityPatch, string> = {
  game_id: "game",
  user_id: "user",
  platform_id: "platform",
  seconds: "duration",
  ended: "ended",
  hidden: "hidden",
};

const unsavedLabels = computed(() =>
  unsavedFieldLabels(patch.value, FIELD_LABELS),
);
useUnsavedChanges("activity", () => unsavedLabels.value);

function revert() {
  if (activity.value) setActivity(activity.value);
}

async function save() {
  if (!activity.value) return;
  const id = activity.value.id;
  try {
    error.value = "";
    message.value = "";
    setActivity(await AdminAPI.patchActivity(id, patch.value));
    message.value = "Saved";
    emit("changed");
  } catch (e: any) {
    error.value = e.message;
  }
}

async function deleteActivity() {
  if (!deleteArmed.value) {
    deleteArmed.value = true;
    return;
  }
  try {
    error.value = "";
    await AdminAPI.deleteActivity(props.activityId);
    emit("deleted");
  } catch (e: any) {
    deleteArmed.value = false;
    error.value = e.message;
  }
}

onMounted(async () => {
  try {
    setActivity(await AdminAPI.getActivity(props.activityId));
    platforms.value = await TimeplayedAPI.getPlatforms({
      limit: 100,
      sort: "name",
    });
  } catch (e: any) {
    error.value = e.message;
  }
});
</script>

<template>
  <div class="card">
    <div class="card-header d-flex align-items-center gap-2">
      <strong class="me-auto">Activity {{ activityId }}</strong>
      <button class="btn-close" @click="emit('close')"></button>
    </div>
    <div class="card-body">
      <div v-if="error" class="alert alert-danger">{{ error }}</div>
      <div v-if="message" class="alert alert-success py-2">{{ message }}</div>

      <template v-if="activity">
        <AdminSectionTabs
          v-model="section"
          :tabs="[
            { id: 'details', label: 'Details', unsaved: unsavedLabels.length },
            { id: 'history', label: `History (${activity.history.length})` },
          ]"
        />
        <template v-if="section === 'details'">
          <dl class="row mb-3 small">
            <dt class="col-sm-3">Started</dt>
            <dd class="col-sm-9">{{ formatDate(activity.started) }}</dd>
            <dt class="col-sm-3">Ended</dt>
            <dd class="col-sm-9">{{ formatDate(activity.ended) }}</dd>
            <dt class="col-sm-3">Created</dt>
            <dd class="col-sm-9">{{ formatDate(activity.created) }}</dd>
          </dl>
          <div class="d-flex flex-wrap gap-2 mb-3">
            <a
              class="btn btn-outline-secondary btn-sm"
              :href="`/activity/${activity.id}`"
              >Activity page</a
            >
            <a
              class="btn btn-outline-secondary btn-sm"
              :href="`/admin?tab=games&id=${activity.game_id}`"
              >Edit game</a
            >
            <a
              class="btn btn-outline-secondary btn-sm"
              :href="`/admin?tab=users&id=${activity.user_id}`"
              >Edit user</a
            >
          </div>

          <div class="row g-2 mb-2">
            <div class="col-6 col-md-3">
              <label class="form-label small mb-0">Game ID</label>
              <input
                v-model="form.game_id"
                class="form-control form-control-sm"
                :class="{ 'border-warning': 'game_id' in patch }"
                type="number"
              />
            </div>
            <div class="col-6 col-md-3">
              <label class="form-label small mb-0">User ID</label>
              <input
                v-model="form.user_id"
                class="form-control form-control-sm"
                :class="{ 'border-warning': 'user_id' in patch }"
                type="number"
              />
            </div>
            <div class="col-12 col-md-6">
              <label class="form-label small mb-0">Platform</label>
              <select
                v-model="form.platform_id"
                class="form-select form-select-sm"
                :class="{ 'border-warning': 'platform_id' in patch }"
              >
                <option v-for="p in platforms" :key="p.id" :value="p.id">
                  {{ p.display_name }} ({{ p.abbreviation }})
                </option>
              </select>
            </div>
            <div class="col-6 col-md-3">
              <label class="form-label small mb-0">Duration (HH:MM:SS)</label>
              <input
                v-model="form.duration"
                class="form-control form-control-sm"
                :class="{ 'border-warning': 'seconds' in patch }"
              />
            </div>
            <div class="col-6 col-md-5">
              <label class="form-label small mb-0">Ended (local time)</label>
              <input
                v-model="form.ended"
                class="form-control form-control-sm"
                :class="{ 'border-warning': 'ended' in patch }"
                type="datetime-local"
                step="1"
              />
            </div>
            <div class="col-12 col-md-4 d-flex align-items-end">
              <div class="form-check">
                <input
                  id="activity-hidden"
                  v-model="form.hidden"
                  class="form-check-input"
                  :class="{ 'border-warning': 'hidden' in patch }"
                  type="checkbox"
                />
                <label class="form-check-label" for="activity-hidden"
                  >Hidden</label
                >
              </div>
            </div>
          </div>
          <div class="d-flex flex-wrap gap-2 mb-3">
            <button class="btn btn-primary btn-sm" @click="save">Save</button>
            <AdminUnsaved :labels="unsavedLabels" @revert="revert" />
            <button
              class="btn btn-outline-danger btn-sm"
              @click="deleteActivity"
            >
              {{ deleteArmed ? "Really delete?" : "Delete activity" }}
            </button>
          </div>
        </template>

        <AdminHistory v-else :history="activity.history" />
      </template>
    </div>
  </div>
</template>
