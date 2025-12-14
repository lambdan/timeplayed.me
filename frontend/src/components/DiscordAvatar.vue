<script lang="ts" setup>
import { onMounted, ref } from "vue";
import type { User } from "../models/models";
import { cacheFetch } from "../utils";

const props = withDefaults(
  defineProps<{ user: User; maxWidth?: number; classes?: string[] }>(),
  {
    maxWidth: 75,
    classes: () => ["img-thumbnail", "img-fluid", "rounded-circle"],
  },
);

const FALLBACK = `https://cdn.discordapp.com/embed/avatars/${
  props.user.id % 5
}.png`;
const avatarUrl = ref<string>(FALLBACK);

onMounted(async () => {
  const res = await cacheFetch(
    `/api/discord/${props.user.id}/avatar`,
    1000 * 60 * 5,
  );
  if (res.ok) {
    const response: { url: string } = await res.json();
    avatarUrl.value = response.url;
  }
});
</script>

<template>
  <a :href="`/user/${props.user.id}`">
    <img
      :src="avatarUrl.toString()"
      :class="[...props.classes]"
      :style="{ maxWidth: props.maxWidth + 'px' }"
      :title="props.user.name"
    />
  </a>
</template>
