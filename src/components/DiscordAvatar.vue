<script lang="ts" setup>
import { onMounted, ref } from "vue";
import type { User } from "../models/models";

const props = withDefaults(defineProps<{ user: User; maxWidth?: number }>(), {
  maxWidth: 75,
});

const FALLBACK = `https://cdn.discordapp.com/embed/avatars/${
  props.user.id % 5
}.png`;
const avatarUrl = ref<string>(FALLBACK);

onMounted(async () => {
  const res = await fetch(`/api/discord/${props.user.id}/avatar`);
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
      class="img-thumbnail img-fluid rounded-circle avatar"
      :style="{ maxWidth: props.maxWidth + 'px' }"
    />
  </a>
</template>
