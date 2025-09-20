<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { User } from "../../models/models";
import DiscordAvatar from "../DiscordAvatar.vue";

const props = withDefaults(
  defineProps<{
    user: User;
  }>(),
  {}
);

const expanded = ref(false);
function toggleExpand() {
  expanded.value = !expanded.value;
}

onMounted(async () => {});
</script>

<template>
  <div class="col-lg-1">
    <div class="row text-center">
      <DiscordAvatar
        :user="props.user"
        :classes="['img-fluid', 'rounded-circle']"
        :maxWidth="75"
      />
    </div>
    <div class="row">
      <a
        :href="`/user/${props.user.id}`"
        class="link-secondary text-center text-decoration-none"
      >
        <strong>{{ props.user.name }}</strong>
      </a>
    </div>
  </div>
</template>
