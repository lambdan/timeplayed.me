<script setup lang="ts">
import { ref } from "vue";
import { AdminAPI, type AdminOverlapGroup } from "../../admin.client";

const PREVIEW_GROUPS = 20;

const error = ref("");
const overlaps = ref<AdminOverlapGroup[]>();
const overlapsMessage = ref("");
const refreshMessage = ref("");

async function call<T>(fn: () => Promise<T>): Promise<T | undefined> {
  try {
    error.value = "";
    return await fn();
  } catch (e: any) {
    error.value = e.message;
  }
}

async function findOverlaps() {
  overlapsMessage.value = "";
  overlaps.value = await call(() => AdminAPI.getOverlaps());
}

async function mergeOverlaps() {
  const res = await call(() => AdminAPI.mergeOverlaps());
  if (res) {
    overlaps.value = undefined;
    overlapsMessage.value = `Merged ${res.groups} groups, ${res.removed} activities removed`;
  }
}

async function refreshSearch() {
  refreshMessage.value = "Refreshing...";
  refreshMessage.value = (await call(() => AdminAPI.refreshSearch())) ?? "";
}
</script>

<template>
  <div>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <h5>Overlapping activities</h5>
    <p class="text-body-secondary small">
      Activities with the same user, game and platform that overlap in time.
      Merging keeps the longest one, spanning from the earliest start to the
      latest end.
    </p>
    <div class="d-flex flex-wrap align-items-center gap-2 mb-2">
      <button class="btn btn-outline-primary btn-sm" @click="findOverlaps">
        Find overlaps
      </button>
      <button
        v-if="overlaps?.length"
        class="btn btn-danger btn-sm"
        @click="mergeOverlaps"
      >
        Merge all
      </button>
      <span v-if="overlapsMessage" class="text-success small">{{
        overlapsMessage
      }}</span>
    </div>
    <div v-if="overlaps" class="mb-4">
      <div v-if="overlaps.length === 0" class="text-body-secondary">
        No overlapping activities
      </div>
      <template v-else>
        <div class="small mb-1">
          {{ overlaps.length }} groups,
          {{ overlaps.reduce((n, g) => n + g.remove_ids.length, 0) }}
          activities would be removed
        </div>
        <ul class="small">
          <li v-for="g in overlaps.slice(0, PREVIEW_GROUPS)" :key="g.keep_id">
            keep
            <a :href="`/admin?tab=activities&id=${g.keep_id}`"
              >#{{ g.keep_id }}</a
            >, remove
            <template v-for="(id, i) in g.remove_ids" :key="id">
              <template v-if="i > 0">, </template>
              <a :href="`/admin?tab=activities&id=${id}`">#{{ id }}</a>
            </template>
          </li>
          <li v-if="overlaps.length > PREVIEW_GROUPS">
            ...and {{ overlaps.length - PREVIEW_GROUPS }} more
          </li>
        </ul>
      </template>
    </div>

    <h5 class="mt-4">Search index</h5>
    <p class="text-body-secondary small">
      Rebuilds the search column of all games, users and platforms.
    </p>
    <div class="d-flex align-items-center gap-2 mb-4">
      <button class="btn btn-outline-primary btn-sm" @click="refreshSearch">
        Refresh search
      </button>
      <span v-if="refreshMessage" class="small">{{ refreshMessage }}</span>
    </div>
  </div>
</template>
