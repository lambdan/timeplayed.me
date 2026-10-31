<script setup lang="ts">
import GameCover from "./GameCover.vue";

// GameCover cropped to a 2:3 box, so covers line up regardless of source
defineProps<{ gameId: number }>();
</script>

<template>
  <div
    class="rounded overflow-hidden bg-body-secondary"
    style="aspect-ratio: 2 / 3"
  >
    <GameCover :gameId="gameId" :maxHeight="0" />
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
  object-fit: scale-down;
}
</style>
