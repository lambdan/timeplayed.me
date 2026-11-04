<script setup lang="ts">
import type { IGDBSearchResult } from "../../admin.client";

defineProps<{ results: IGDBSearchResult[] }>();
const emit = defineEmits<{ use: [igdbId: number] }>();

function year(ts: number | null) {
  // igdb gives seconds
  return ts ? new Date(ts * 1000).getUTCFullYear() : "?";
}

function thumbnail(imageId: string) {
  return `https://images.igdb.com/igdb/image/upload/t_cover_small/${imageId}.jpg`;
}
</script>

<template>
  <ul class="list-group list-group-flush">
    <li v-if="results.length === 0" class="list-group-item px-0">No results</li>
    <li
      v-for="r in results"
      :key="r.id"
      class="list-group-item px-0 d-flex align-items-center gap-2"
    >
      <img
        v-if="r.cover"
        :src="thumbnail(r.cover.image_id)"
        :alt="r.name"
        width="45"
        height="64"
        class="rounded flex-shrink-0 object-fit-cover"
      />
      <img
        v-else
        src="https://placehold.co/90x128?text=?"
        alt="No cover"
        width="45"
        height="64"
        class="rounded flex-shrink-0"
      />
      <div class="me-auto">
        <a :href="r.url" target="_blank">{{ r.name }}</a>
        <div class="small text-body-secondary">
          {{ year(r.first_release_date) }} · IGDB {{ r.id }}
        </div>
      </div>
      <button class="btn btn-primary" @click="emit('use', r.id)">Use</button>
    </li>
  </ul>
</template>
