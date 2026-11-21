<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { TimeplayedAPI } from "../../api.client";
import type { GameCover } from "../../api.models";
import { useNsfw } from "../../composables/useNsfw";

const props = withDefaults(
  defineProps<{
    gameId: number;
    clickable?: boolean;
    maxHeight?: number;
    maxWidth?: number;
    /** shown small (like in lists), so a smaller version of the cover is enough */
    thumbnail?: boolean;
    /** where the cover is from, under it */
    showCredits?: boolean;
  }>(),
  {
    clickable: true,
    maxWidth: 0,
    maxHeight: 400,
  },
);

const DISABLED_COVER = `https://placehold.co/600x900?text=Cover+art+disabled\\nfor+this+game`;
const NO_COVER = `https://placehold.co/600x900?text=No+cover+art\\n...yet`;
const game = ref<{ nsfw: boolean; cover_disabled: boolean }>();
const { isCensored } = useNsfw();

// the preview (a few pixels, shown blurred) right away. The full cover once we know the game,
// and that it's not NSFW (or the viewer opted in to see NSFW)
const previewUrl = computed(() =>
  TimeplayedAPI.gameCoverUrl(props.gameId, "preview"),
);
const fullUrl = computed(() => {
  if (!game.value || isCensored(game.value)) return undefined;
  const version = props.thumbnail ? "thumbnail" : "display";
  return TimeplayedAPI.gameCoverUrl(props.gameId, version);
});
// the preview is a 404 when the game has no cover
const noCover = ref(false);

// the full cover is loaded on the side, the preview is shown until it's done
const fullLoaded = ref(false);
watch(
  fullUrl,
  (url) => {
    fullLoaded.value = false;
    if (!url) return;
    const full = new Image();
    full.onload = () => {
      if (fullUrl.value === url) fullLoaded.value = true;
    };
    full.onerror = () => {
      if (fullUrl.value === url) noCover.value = true;
    };
    full.src = url;
    // already in the browser's cache, then don't flash the preview
    if (full.complete && full.naturalWidth > 0) fullLoaded.value = true;
  },
  { immediate: true },
);

const placeholder = computed(() => {
  if (game.value?.cover_disabled) return DISABLED_COVER;
  if (noCover.value) return NO_COVER;
  return undefined;
});
const showingPreview = computed(() => !placeholder.value && !fullLoaded.value);
const imageUrl = computed(() => {
  if (placeholder.value) return placeholder.value;
  if (showingPreview.value) return previewUrl.value;
  return fullUrl.value!;
});
function onError() {
  if (imageUrl.value === previewUrl.value) noCover.value = true;
}

// a share of the width so it's equally blurry at every size. starts strong, and is set
// from the real width once the preview is loaded
const BLUR_SHARE = 0.06;
const blurPx = ref(20);
function onLoad(event: Event) {
  const img = event.target as HTMLImageElement;
  if (img.clientWidth > 0) {
    blurPx.value = img.clientWidth * BLUR_SHARE;
  }
}
// the preview is a few pixels large, so it's always shown blurred,
// and stretched to the size the cover would have
const blurred = showingPreview;
function previewSize() {
  if (props.maxHeight) return { height: props.maxHeight + "px" };
  if (props.maxWidth) return { width: props.maxWidth + "px" };
  // CroppedCover stretches it already
  return {};
}
const imgStyle = computed(() => {
  const style = {
    maxHeight: props.maxHeight ? props.maxHeight + "px" : undefined,
    maxWidth: props.maxWidth ? props.maxWidth + "px" : undefined,
  };
  if (!blurred.value) {
    return style;
  }
  return {
    ...style,
    ...previewSize(),
    filter: `blur(${blurPx.value}px)`,
    // scaled up a bit, so the blurry edges are cut off by the overflow-hidden wrapper
    transform: "scale(1.15)",
  };
});
// only IGDB's are credited, uploaded covers can be from anywhere
const cover = ref<GameCover>();
const credits = computed(() => {
  if (!game.value || isCensored(game.value)) return undefined;
  if (cover.value?.source !== "IGDB") return undefined;
  return cover.value.credits ?? undefined;
});

async function load() {
  noCover.value = false;
  game.value = await TimeplayedAPI.getGame(props.gameId).catch(() => undefined);
  if (props.showCredits) {
    cover.value = await TimeplayedAPI.getGameCover(props.gameId).catch(
      () => undefined,
    );
  }
}

onMounted(load);
watch(() => props.gameId, load);
</script>

<template>
  <div style="display: inline-block">
    <div
      :class="{ 'overflow-hidden': blurred }"
      style="display: inline-block; position: relative"
    >
      <a v-if="clickable" :href="`/game/${props.gameId}`">
        <img
          v-show="imageUrl"
          :src="`${imageUrl}`"
          class="img-fluid"
          :style="imgStyle"
          @load="onLoad"
          @error="onError"
        />
      </a>
      <img
        v-else
        v-show="imageUrl"
        :src="`${imageUrl}`"
        class="img-fluid"
        :style="imgStyle"
        @load="onLoad"
        @error="onError"
      />
    </div>
    <div v-if="credits" class="small text-body-secondary" :title="credits">
      Cover from IGDB
    </div>
  </div>
</template>
