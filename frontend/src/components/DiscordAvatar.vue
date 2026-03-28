<script lang="ts" setup>
import type { User } from "../api.models";
import { onMounted, ref } from "vue";

const avatarUrl = ref<string>();

const props = withDefaults(
  defineProps<{ user: User; maxWidth?: number; classes?: string[] }>(),
  {
    maxWidth: 75,
    classes: () => ["img-thumbnail", "img-fluid", "rounded-circle"],
  },
);

onMounted(() => {
  if (props.user.discord_id) {
    avatarUrl.value = `/api/discord/avatar/${props.user.discord_id}`;
  } else {
    avatarUrl.value = "https://placehold.co/512x512?text=" + props.user.name;
  }
});
</script>

<template>
  <a :href="`/user/${props.user.id}`" v-if="avatarUrl">
    <img
      :src="avatarUrl"
      :class="[...props.classes]"
      :style="{ maxWidth: props.maxWidth + 'px' }"
      :title="props.user.name"
    />
  </a>
</template>
