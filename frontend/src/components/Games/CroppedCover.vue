<script setup lang="ts">
import GameCover from "./GameCover.vue";

// GameCover cropped to a 2:3 box, so covers line up regardless of source
withDefaults(
  defineProps<{ gameId: number; clickable?: boolean; thumbnail?: boolean }>(),
  { clickable: true },
);
</script>

<template>
  <div
    class="rounded overflow-hidden bg-body-secondary"
    style="aspect-ratio: 2 / 3"
  >
    <GameCover
      :gameId="gameId"
      :maxHeight="0"
      :clickable="clickable"
      :thumbnail="thumbnail"
    />
  </div>
</template>

<style scoped>
/* GameCover wraps the img in a div and a link, stretch them all to fill the box */
:deep(div),
:deep(a),
:deep(img) {
  display: block !important;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* Safari ignores height: 100% on the img, so it would render at its natural height */
:deep(img) {
  position: absolute;
  top: 0;
  left: 0;
}
</style>
