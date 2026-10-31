<script setup lang="ts">
import type { Activity } from "../api.models";
import { formatDuration } from "../utils";
import { heatBadgeStyle } from "../utils.heat";
import { useLookups } from "../composables/useLookups";
import DiscordAvatar from "./DiscordAvatar.vue";
import CroppedCover from "./Games/CroppedCover.vue";
import PlatformBadge from "./Badges/PlatformBadge.vue";

// one activity in a list. the last cell (when it happened) is up to the list, as a slot
const props = withDefaults(
  defineProps<{
    activity: Activity;
    /** hide on the users own page, it's redundant there */
    showUser?: boolean;
    /** hide on the games own page */
    showGame?: boolean;
    /** hide on the platforms own page */
    showPlatform?: boolean;
    /** duration to show, if not the whole activity (like the part played on one day) */
    seconds?: number;
  }>(),
  { showUser: true, showGame: true, showPlatform: true },
);

const lookups = useLookups();
const shown = () => props.seconds ?? props.activity.seconds;
</script>

<template>
  <tr>
    <td v-if="showUser" style="width: 50px">
      <DiscordAvatar
        v-if="lookups.user(activity.user_id)"
        :user="lookups.user(activity.user_id)!"
        :maxWidth="40"
      />
    </td>
    <td v-if="showGame" class="d-none d-md-table-cell" style="width: 50px">
      <CroppedCover :gameId="activity.game_id" style="width: 32px" />
    </td>
    <td v-if="showGame" class="w-100 text-break">
      <a
        :href="`/game/${activity.game_id}`"
        class="link-underline link-underline-opacity-0"
        >{{ lookups.game(activity.game_id)?.name }}</a
      >
    </td>
    <!-- without the game (on its own page) there's room for the name of who played -->
    <td v-else-if="showUser" class="w-100 text-break">
      <a
        :href="`/user/${activity.user_id}`"
        class="link-underline link-underline-opacity-0"
        >{{ lookups.user(activity.user_id)?.display_name }}</a
      >
    </td>
    <!-- width 1% = only as wide as the content, so these stay together at the end -->
    <td v-if="showPlatform" class="d-none d-md-table-cell" style="width: 1%">
      <PlatformBadge
        v-if="lookups.platform(activity.platform_id)"
        :platform="lookups.platform(activity.platform_id)!"
        :showName="false"
      />
    </td>
    <td class="text-nowrap px-md-3" style="width: 1%">
      <!-- colored by length, same scale as the recap heatmap -->
      <a
        :href="`/activity/${activity.id}`"
        class="badge fw-semibold text-decoration-none"
        :style="{
          ...heatBadgeStyle(shown()),
          fontVariantNumeric: 'tabular-nums',
        }"
        :title="`${activity.seconds} seconds`"
        >{{ formatDuration(shown(), true) }}</a
      >
    </td>
    <td class="text-nowrap" style="width: 1%">
      <slot />
    </td>
  </tr>
</template>
