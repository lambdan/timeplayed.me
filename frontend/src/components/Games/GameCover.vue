<script setup lang="ts">
import { onMounted, ref } from "vue";
import { getGameCoverData } from "../../utils";
import type { GameCoverData } from "../../api.models";

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

const LOADING_COVER = `https://placehold.co/600x900?text=Loading...`;
const clickable = ref(props.clickable);
const imageUrl = ref<string>(LOADING_COVER);
const coverData = ref<GameCoverData>();
const creditsText = ref("...");
const sourceUrl = ref<string>();

onMounted(async () => {
  coverData.value = await getGameCoverData(props.gameId, props.thumb);
  imageUrl.value = coverData.value.imageUrl;

  sourceUrl.value = coverData.value.sourceUrl;
  creditsText.value = `Source: ${coverData.value.source}.`;
  if (coverData.value.credits) {
    creditsText.value += " " + coverData.value.credits;
  }
});
</script>

<template>
  <div style="display: inline-block; position: relative">
    <template v-if="clickable">
      <a :href="`/game/${props.gameId}`">
        <img
          v-show="imageUrl"
          :title="creditsText"
          :src="`${imageUrl}`"
          class="img-fluid"
          :style="{
            maxHeight: props.maxHeight ? props.maxHeight + 'px' : undefined,
            maxWidth: props.maxWidth ? props.maxWidth + 'px' : undefined,
          }"
        />
      </a>
    </template>
    <template v-else-if="sourceUrl">
      <a :href="sourceUrl">
        <img
          v-show="imageUrl"
          :src="`${imageUrl}`"
          :title="creditsText"
          class="img-fluid"
          :style="{
            maxHeight: props.maxHeight ? props.maxHeight + 'px' : undefined,
            maxWidth: props.maxWidth ? props.maxWidth + 'px' : undefined,
          }"
        />
      </a>
    </template>
    <template v-else>
      <img
        v-show="imageUrl"
        :src="`${imageUrl}`"
        :title="creditsText"
        class="img-fluid"
        :style="{
          maxHeight: props.maxHeight ? props.maxHeight + 'px' : undefined,
          maxWidth: props.maxWidth ? props.maxWidth + 'px' : undefined,
        }"
      />
    </template>
  </div>
</template>
