<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { Game, SGDBGame, SGDBGrid } from "../../models/models";
import { cacheFetch, getGameCoverUrl } from "../../utils";

const props = withDefaults(
  defineProps<{
    game: Game;
    thumb?: boolean;
    clickable?: boolean;
    maxHeight?: number;
    maxWidth?: number;
  }>(),
  {
    thumb: false,
    clickable: true,
    maxWidth: 0,
    maxHeight: 400
  }
);

const CACHE_LIFETIME = 1000 * 60 * 60; // 1 hour
const clickable = ref(props.clickable);
const imageUrl = ref<string>("");
const loading = ref(true);


onMounted(async () => {
  imageUrl.value = await getGameCoverUrl(props.game.id, props.thumb);
  loading.value = false;
});
</script>

<template>
  <div style="display: inline-block; position: relative">
    <template v-if="clickable">
      <a :href="`/game/${props.game.id}`">
        <div v-if="loading" class="spinner-border" role="status"></div>
        <img
          v-show="!loading"
          :src="`${imageUrl}`"
          class="img-fluid"
          :style="{
            maxHeight: props.maxHeight ? props.maxHeight + 'px' : undefined,
            maxWidth: props.maxWidth ? props.maxWidth + 'px' : undefined
          }"
        />
      </a>
    </template>
    <template v-else>
      <div>
        <div v-if="loading" class="spinner-border" role="status"></div>
        <img
          v-show="!loading"
          :src="`${imageUrl}`"
          class="img-fluid"
          :style="{
            maxHeight: props.maxHeight ? props.maxHeight + 'px' : undefined,
            maxWidth: props.maxWidth ? props.maxWidth + 'px' : undefined
          }"
        />
      </div>
    </template>
  </div>
</template>
