<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { AdminAPI, type AdminActivity } from "../../admin.client";
import { useLookups } from "../../composables/useLookups";
import { formatDate, formatDuration } from "../../utils";
import AdminActivityEditor from "./AdminActivityEditor.vue";

const PAGE_SIZE = 100;

const route = useRoute();
const router = useRouter();
const lookups = useLookups();

const activities = ref<AdminActivity[]>([]);
const hasMore = ref(false);
const error = ref("");

// filters, strings because they're bound to inputs
const filters = ref({ user: "", game: "", platform: "" });
const openId = ref("");
const selectedId = ref<number>();

function asNumber(s: string) {
  return parseInt(s) || undefined;
}

function filterQuery() {
  return {
    user: asNumber(filters.value.user),
    game: asNumber(filters.value.game),
    platform: asNumber(filters.value.platform),
  };
}

async function fetchActivities(append = false) {
  try {
    error.value = "";
    const offset = append ? activities.value.length : 0;
    const page = await AdminAPI.getActivities({
      ...filterQuery(),
      offset,
      limit: PAGE_SIZE,
    });
    activities.value = append ? [...activities.value, ...page] : page;
    hasMore.value = page.length === PAGE_SIZE;
  } catch (e: any) {
    error.value = e.message;
  }
}

function updateQuery(id?: number) {
  router.replace({ query: { tab: "activities", ...filterQuery(), id } });
}

function select(id?: number) {
  updateQuery(id);
  // the editor is above the list
  if (id) window.scrollTo({ top: 0, behavior: "smooth" });
}

function applyFilters() {
  updateQuery(selectedId.value);
  fetchActivities();
}

function openActivity() {
  const id = asNumber(openId.value);
  if (id) select(id);
}

watch(
  () => route.query.id,
  () => {
    selectedId.value = asNumber(route.query.id as string);
  },
  { immediate: true },
);

onMounted(() => {
  for (const key of ["user", "game", "platform"] as const) {
    filters.value[key] = (route.query[key] as string) ?? "";
  }
  fetchActivities();
});
</script>

<template>
  <div>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <AdminActivityEditor
      v-if="selectedId"
      :key="selectedId"
      :activity-id="selectedId"
      class="mb-3"
      @close="select(undefined)"
      @changed="fetchActivities()"
      @deleted="
        select(undefined);
        fetchActivities();
      "
    />

    <div class="row g-2 mb-2">
      <div class="col-6 col-md-2">
        <input
          v-model="filters.user"
          class="form-control"
          type="number"
          placeholder="User ID"
          @keydown.enter="applyFilters"
        />
      </div>
      <div class="col-6 col-md-2">
        <input
          v-model="filters.game"
          class="form-control"
          type="number"
          placeholder="Game ID"
          @keydown.enter="applyFilters"
        />
      </div>
      <div class="col-6 col-md-2">
        <input
          v-model="filters.platform"
          class="form-control"
          type="number"
          placeholder="Platform ID"
          @keydown.enter="applyFilters"
        />
      </div>
      <div class="col-6 col-md-2">
        <button class="btn btn-outline-primary w-100" @click="applyFilters">
          Filter
        </button>
      </div>
      <div class="col-12 col-md-4">
        <div class="input-group">
          <input
            v-model="openId"
            class="form-control"
            type="number"
            placeholder="Activity ID"
            @keydown.enter="openActivity"
          />
          <button class="btn btn-outline-secondary" @click="openActivity">
            Open
          </button>
        </div>
      </div>
    </div>

    <div class="table-responsive">
      <table class="table table-hover table-sm align-middle">
        <thead>
          <tr>
            <th>ID</th>
            <th>Ended</th>
            <th>Duration</th>
            <th>Game</th>
            <th class="d-none d-md-table-cell">User</th>
            <th class="d-none d-md-table-cell">Platform</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="a in activities"
            :key="a.id"
            role="button"
            :class="{ 'table-active': selectedId === a.id }"
            @click="select(a.id)"
          >
            <td>{{ a.id }}</td>
            <td class="text-nowrap">{{ formatDate(a.ended) }}</td>
            <td class="text-nowrap">{{ formatDuration(a.seconds, true) }}</td>
            <td>
              {{ lookups.game(a.game_id)?.name ?? `#${a.game_id}` }}
              <span v-if="a.hidden" class="badge text-bg-warning">hidden</span>
            </td>
            <td class="d-none d-md-table-cell">
              {{ lookups.user(a.user_id)?.display_name ?? `#${a.user_id}` }}
            </td>
            <td class="d-none d-md-table-cell">
              {{
                lookups.platform(a.platform_id)?.display_name ??
                `#${a.platform_id}`
              }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="activities.length === 0" class="text-body-secondary">
      No activities found
    </div>
    <button
      v-if="hasMore"
      class="btn btn-outline-secondary btn-sm"
      @click="fetchActivities(true)"
    >
      Load more
    </button>
  </div>
</template>
