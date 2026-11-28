<script lang="ts" setup>
import { TimeplayedAPI } from "../api.client";
import type { User } from "../api.models";
import { onMounted, ref } from "vue";

const avatarUrl = ref<string>();

const props = withDefaults(
  defineProps<{
    user: User;
    maxWidth?: number;
    classes?: string[];
    /** link to the users page */
    link?: boolean;
  }>(),
  {
    maxWidth: 75,
    link: true,
    classes: () => ["img-thumbnail", "img-fluid", "rounded-circle"],
  },
);

onMounted(async () => {
  // anonymous users have no Discord ID: one of Discord's default avatars
  avatarUrl.value = `https://cdn.discordapp.com/embed/avatars/${props.user.id % 5}.png`;
  if (props.user.discord_id) {
    avatarUrl.value = TimeplayedAPI.getDiscordAvatarUrl(props.user.discord_id);
  }
});
</script>

<template>
  <component
    :is="props.link ? 'a' : 'span'"
    :href="props.link ? `/user/${props.user.id}` : undefined"
    v-if="avatarUrl"
  >
    <img
      :src="avatarUrl"
      :class="[...props.classes]"
      :style="{ maxWidth: props.maxWidth + 'px' }"
      :title="props.user.display_name"
    />
  </component>
</template>
