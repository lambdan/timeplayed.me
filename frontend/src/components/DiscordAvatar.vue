<script lang="ts" setup>
import { TimeplayedAPI } from "../api.client";
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

onMounted(async () => {
  avatarUrl.value = "https://placehold.co/512x512?text=" + props.user.name;
  if (props.user.discord_id) {
    avatarUrl.value = TimeplayedAPI.getDiscordAvatarUrl(props.user.discord_id);
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
