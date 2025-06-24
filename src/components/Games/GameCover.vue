<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { Game, SGDBGame, SGDBGrid } from "../../models/models";

const FALLBACK = "https://placehold.co/267x400?text=No+Image";

const props = withDefaults(defineProps<{ game: Game; thumb?: boolean }>(), {
  thumb: false,
});

const imageUrl = ref<string>("");
const loading = ref(true);

async function getCover(): Promise<string> {
  if (props.game.image_url) {
    return props.game.image_url;
  }

  if (props.game.steam_id) {
    return `https://shared.steamstatic.com/store_item_assets/steam/apps/${props.game.steam_id}/library_600x900.jpg`;
  }

  if (props.game.sgdb_id) {
    const res = await fetch(`/api/sgdb/grids/${props.game.sgdb_id}/best`);
    if (res.ok) {
      const data: SGDBGrid = await res.json();
      return props.thumb ? data.thumbnail : data.url;
    }
    return FALLBACK;
  }

  // search
  const searchRes = await fetch(
    `/api/sgdb/search?query=${encodeURIComponent(props.game.name)}`
  );

  if (searchRes.ok) {
    const searchData: SGDBGame[] = await searchRes.json();
    if (searchData.length > 0) {
      const gameId = searchData[0].id;
      const res = await fetch(`/api/sgdb/grids/${gameId}/best`);
      if (res.ok) {
        const data: SGDBGrid = await res.json();
        return props.thumb ? data.thumbnail : data.url;
      }
    }
  }

  return FALLBACK;
}

onMounted(async () => {
  imageUrl.value = await getCover();
  loading.value = false;
});
</script>

<template>
  <a
    :href="`/game/${props.game.id}`"
    style="display: inline-block; position: relative"
  >
    <div v-if="loading" class="spinner-border" role="status"></div>
    <img v-show="!loading" :src="`${imageUrl}`" class="img-fluid" />
  </a>
</template>
