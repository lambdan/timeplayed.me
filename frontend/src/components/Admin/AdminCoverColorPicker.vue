<script setup lang="ts">
import { computed, ref } from "vue";
import { TimeplayedAPI } from "../../api.client";
import { pickColors, type TileColors } from "../../coverColors";

// the game's cover: clicking it picks the color at that spot, Auto picks both colors
const props = defineProps<{
  gameId: number;
  /** what clicking the cover sets, like "background" */
  target: string;
}>();
const emit = defineEmits<{
  pick: [color: string];
  auto: [colors: TileColors];
}>();

// a few pixels around the spot are averaged, so a single odd pixel isn't picked
const RADIUS = 2;

const url = computed(() => TimeplayedAPI.gameCoverUrl(props.gameId, "display"));
const canvas = document.createElement("canvas");
const loaded = ref(false);
const failed = ref(false);
// the colors Auto picked, best first, and which one was used last
const autoColors = ref<TileColors[]>([]);
const autoIndex = ref(0);

function onLoad(event: Event) {
  const image = event.target as HTMLImageElement;
  canvas.width = image.naturalWidth;
  canvas.height = image.naturalHeight;
  canvas.getContext("2d")?.drawImage(image, 0, 0);
  loaded.value = true;
  // a new cover, Auto picks again
  autoColors.value = [];
}

function hex(value: number) {
  return Math.round(value).toString(16).padStart(2, "0");
}

function onClick(event: MouseEvent) {
  const context = canvas.getContext("2d");
  if (!loaded.value || !context) return;
  const image = event.target as HTMLImageElement;
  const rect = image.getBoundingClientRect();
  const x = Math.floor(
    ((event.clientX - rect.left) / rect.width) * canvas.width,
  );
  const y = Math.floor(
    ((event.clientY - rect.top) / rect.height) * canvas.height,
  );
  const left = Math.max(0, x - RADIUS);
  const top = Math.max(0, y - RADIUS);
  const width = Math.min(canvas.width, x + RADIUS + 1) - left;
  const height = Math.min(canvas.height, y + RADIUS + 1) - top;
  const pixels = context.getImageData(left, top, width, height).data;
  const sum = [0, 0, 0];
  for (let i = 0; i < pixels.length; i += 4) {
    sum[0] += pixels[i];
    sum[1] += pixels[i + 1];
    sum[2] += pixels[i + 2];
  }
  const count = pixels.length / 4;
  emit("pick", "#" + sum.map((s) => hex(s / count)).join(""));
}

/** the best colors first, each click tries the next */
async function auto() {
  if (autoColors.value.length === 0) {
    autoColors.value = await pickColors(url.value);
    autoIndex.value = 0;
  } else {
    autoIndex.value = (autoIndex.value + 1) % autoColors.value.length;
  }
  const colors = autoColors.value[autoIndex.value];
  if (colors) emit("auto", colors);
}
</script>

<template>
  <div v-if="failed" class="text-body-secondary small">No cover</div>
  <template v-else>
    <img
      :src="url"
      alt="Cover"
      class="img-fluid rounded d-block"
      style="max-height: 240px; cursor: crosshair"
      @load="onLoad"
      @error="failed = true"
      @click="onClick"
    />
    <div class="small text-body-secondary">
      Click to pick the {{ target }} color
    </div>
    <button
      class="btn btn-outline-secondary btn-sm mt-1"
      :disabled="!loaded"
      @click="auto"
    >
      Auto
      <span v-if="autoColors.length > 1"
        >({{ autoIndex + 1 }}/{{ autoColors.length }})</span
      >
    </button>
  </template>
</template>
