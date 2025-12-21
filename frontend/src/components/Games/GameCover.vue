<script setup lang="ts">
import { onMounted, ref } from "vue";
import { getGameCoverUrl } from "../../utils";

const props = withDefaults(
  defineProps<{
    gameId: number;
    thumb?: boolean;
    clickable?: boolean;
    maxHeight?: number;
    maxWidth?: number;
  }>(),
  {
    thumb: false,
    clickable: true,
    maxWidth: 0,
    maxHeight: 400,
  },
);

const FALLBACK = `https://placehold.co/600x900?text=Loading...`;
const clickable = ref(props.clickable);
const imageUrl = ref<string>(FALLBACK);

onMounted(async () => {
  imageUrl.value = await getGameCoverUrl(props.gameId, props.thumb);
});
</script>

<template>
  <div style="display: inline-block; position: relative">
    <template v-if="clickable">
      <a :href="`/game/${props.gameId}`">
        <img
          v-show="imageUrl"
          :src="`${imageUrl}`"
          class="img-fluid"
          :style="{
            maxHeight: props.maxHeight ? props.maxHeight + 'px' : undefined,
            maxWidth: props.maxWidth ? props.maxWidth + 'px' : undefined,
          }"
        />
      </a>
    </template>
    <template v-else>
      <div>
        <img
          v-show="imageUrl"
          :src="`${imageUrl}`"
          class="img-fluid"
          :style="{
            maxHeight: props.maxHeight ? props.maxHeight + 'px' : undefined,
            maxWidth: props.maxWidth ? props.maxWidth + 'px' : undefined,
          }"
        />
      </div>
    </template>
  </div>
</template>
