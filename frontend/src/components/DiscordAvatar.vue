<script lang="ts" setup>
import { onMounted, ref } from "vue";
import type { User } from "../api.models";
import { TimeplayedAPI } from "../api.client";

const avatarUrl = ref<string>();

const props = withDefaults(
  defineProps<{ user: User; maxWidth?: number; classes?: string[] }>(),
  {
    maxWidth: 75,
    classes: () => ["img-thumbnail", "img-fluid", "rounded-circle"],
  },
);

function getSessionStorageAvatar(discordUserId: string): string | null {
  const stored = sessionStorage.getItem(`discord_avatar_${discordUserId}`);
  if (stored) {
    return stored;
  }
  return null;
}

function storeSessionStorageAvatar(discordUserId: string, avatarUrl: string) {
  sessionStorage.setItem(`discord_avatar_${discordUserId}`, avatarUrl);
}

function setFetchLock(discordUserId: string, state: boolean) {
  sessionStorage.setItem(
    `discord_avatar_fetching_${discordUserId}`,
    `${state}`,
  );
}

function isFetching(discordUserId: string): boolean {
  const lock = sessionStorage.getItem(
    `discord_avatar_fetching_${discordUserId}`,
  );
  return lock === "true";
}

let FALLBACK = `https://cdn.discordapp.com/embed/avatars/0.png`;
if (props.user && props.user.id && !isNaN(+props.user.id)) {
  FALLBACK = `https://cdn.discordapp.com/embed/avatars/${
    +props.user.id % 5
  }.png`;
}

onMounted(async () => {
  function tryGetStored(): boolean {
    // use stored if available
    const stored = getSessionStorageAvatar(props.user.id);
    if (stored) {
      avatarUrl.value = stored;
      return true;
    }
    return false;
  }

  if (tryGetStored()) {
    return; // we got it
  }

  let waited = 0;
  const delay = 10;
  while (isFetching(props.user.id)) {
    //console.log("Someone else is fetching the avatar for", props.user.id);
    await new Promise((resolve) => setTimeout(resolve, delay));
    if (tryGetStored()) {
      return; // we got it
    }
    waited += delay;
    if (waited > 3000) {
      break; // give up and try to fetch it as well...
    }
  }

  //console.log("Fetching avatar for", props.user.id);

  setFetchLock(props.user.id, true);

  // else: fetch it and store it
  const { data, error } = await TimeplayedAPI.getClient().GET(
    "/api/discord/{discord_user_id}/avatar",
    {
      params: {
        path: {
          discord_user_id: props.user.id,
        },
      },
    },
  );
  if (data && data.url) {
    storeSessionStorageAvatar(props.user.id, data.url);
  } else {
    avatarUrl.value = FALLBACK;
  }

  // reset the lock again
  setFetchLock(props.user.id, false);
});
</script>

<template>
  <a :href="`/user/${props.user.id}`" v-if="avatarUrl">
    <img
      :src="avatarUrl.toString()"
      :class="[...props.classes]"
      :style="{ maxWidth: props.maxWidth + 'px' }"
      :title="props.user.name"
    />
  </a>
</template>
