<script setup lang="ts">
import { getRecapYear } from "../utils";
import DiscordAvatar from "./DiscordAvatar.vue";
import type { UserWithStats } from "../api.models";
import AdminEditLink from "./Misc/AdminEditLink.vue";
import InfoStatTiles from "./Misc/InfoStatTiles.vue";
import PlayingNowTiles from "./Users/PlayingNowTiles.vue";

defineProps<{ user: UserWithStats }>();

const recapYear = getRecapYear();
</script>

<template>
  <div class="card">
    <h1 class="card-header d-flex align-items-center gap-2">
      <div class="me-auto">
        {{ user.display_name }}
        <!-- the display name is the title already -->
        <span
          v-if="user.name !== user.display_name"
          class="text-muted d-block"
          style="font-size: 0.5em"
          >{{ user.name }}</span
        >
      </div>
      <AdminEditLink tab="users" :id="user.id" />
      <a
        v-if="recapYear"
        :href="`/user/${user.id}/recap/${recapYear}`"
        class="btn btn-success"
        >Recap {{ recapYear }}</a
      >
    </h1>
    <div class="card-body">
      <div class="row g-3">
        <div class="col-12 col-sm-auto text-center">
          <DiscordAvatar :user="user" :maxWidth="200" />
        </div>
        <div class="col">
          <InfoStatTiles
            :stats="user.stats"
            :counts="[
              { label: 'Games', value: user.stats.game_count },
              { label: 'Platforms', value: user.stats.platform_count },
            ]"
          >
            <PlayingNowTiles :userId="user.id" />
          </InfoStatTiles>
        </div>
      </div>
    </div>
  </div>
</template>
