<script setup lang="ts">
import { onMounted, ref } from "vue";
import { formatDuration, timeAgo } from "../../utils";
import DiscordAvatar from "../DiscordAvatar.vue";
import GameCover from "../Games/GameCover.vue";
import PlatformBadge from "../Badges/PlatformBadge.vue";
import type {
  Activity,
  GameWithStats,
  PlatformWithStats,
  User,
  UserWithStats,
} from "../../api.models";

const props = defineProps<{
  activity?: Activity;
  game?: GameWithStats;
  user?: UserWithStats;
  platform?: PlatformWithStats;
  durationSeconds?: number;
  showDate?: boolean;
  date?: Date;
  context?:
    | "userPage"
    | "gamePage"
    | "frontPage"
    | "gameTable"
    | "userTable"
    | "platformTable";
}>();

const _id = ref<string | number>("");
const _durationSeconds = ref(0);
const _timeDisplayed = ref("");
const _dateDisplayed = ref("");
const _date = ref<Date>();

function updateDate(d: Date) {
  _dateDisplayed.value = timeAgo(d, true);
}

function setupActivity(activity: Activity) {
  _timeDisplayed.value = formatDuration(activity.seconds);
  updateDate(new Date(activity.timestamp));
  setInterval(() => {
    updateDate(new Date(activity.timestamp));
  }, 1000); // Update every second
}

function setupDuration() {
  if (props.durationSeconds) {
    _durationSeconds.value = props.durationSeconds;
  } else if (props.activity) {
    _durationSeconds.value = props.activity.seconds;
  } else if (props.game) {
    _durationSeconds.value = props.game.totals.playtime_secs;
  } else {
    throw new Error("Either activity or duration prop must be provided");
  }
  _timeDisplayed.value = formatDuration(_durationSeconds.value);
}

function shouldShowGameCover(): boolean {
  return getGameCoverId() >= 0;
}

/** Returns -1 if game cover should not be shown */
function getGameCoverId(): number {
  if (props.context === "userPage" && props.activity) {
    return props.activity.game.id;
  }
  if (props.context === "gameTable" && props.game) {
    return props.game.game.id;
  }
  return -1;
}

function shouldShowAvatar(): boolean {
  if (props.user && props.user.user) {
    return true;
  }
  if (props.context !== "userPage" && props.activity) {
    return true;
  }
  return false;
}

function getUserForDiscordAvatar(): User {
  if (props.user && props.user.user) {
    return props.user.user;
  }
  if (props.activity) {
    return props.activity.user;
  }
  throw new Error("No user available for DiscordAvatar");
}

onMounted(() => {
  if (props.date) {
    _date.value = props.date;
    updateDate(props.date);
  }

  if (props.activity) {
    _id.value = props.activity.id;
    setupActivity(props.activity);
  } else if (props.user) {
    _id.value = props.user.user.id;
  } else if (props.game) {
    _id.value = props.game.game.id;
  } else if (props.platform) {
    _id.value = props.platform.platform.id;
  }

  setupDuration();
});
</script>

<template>
  <tr class="align-middle" :key="_id">
    <td v-if="props.activity">
      <small title="Activity ID" class="text-secondary">{{
        props.activity.id
      }}</small>
    </td>

    <td v-if="shouldShowAvatar()">
      <DiscordAvatar
        :user="getUserForDiscordAvatar()"
        :maxWidth="50"
      ></DiscordAvatar>
    </td>

    <td v-if="props.platform">
      <PlatformBadge :platform="props.platform.platform" :showName="false" />
    </td>

    <td v-if="props.platform">
      <a
        :href="`/platform/${props.platform!.platform.id}`"
        class="link-underline link-underline-opacity-0"
        >{{
          props.platform!.platform.name || props.platform!.platform.abbreviation
        }}</a
      >
    </td>

    <td
      v-if="
        props.user &&
        (props.context === 'frontPage' || props.context === 'gamePage')
      "
    >
      <a
        :href="`/user/${props.user!.user.id}`"
        class="link-underline link-underline-opacity-0"
        >{{ props.user!.user.name }}</a
      >
    </td>

    <td v-if="shouldShowGameCover()">
      <GameCover
        :gameId="getGameCoverId()"
        :thumb="true"
        :maxHeight="50"
      ></GameCover>
    </td>

    <td v-if="props.context !== 'gamePage' && props.activity">
      <a
        :href="`/game/${props.activity.game.id}`"
        class="link-underline link-underline-opacity-0"
        >{{ props.activity.game.name }}</a
      >
    </td>

    <td v-if="props.game">
      <a
        :href="`/game/${props.game.game.id}`"
        class="link-underline link-underline-opacity-0"
        >{{ props.game.game.name }}</a
      >
    </td>

    <td v-if="props.user && props.context === 'userTable'">
      <a
        :href="`/user/${props.user!.user.id}`"
        class="link-underline link-underline-opacity-0"
        >{{ props.user!.user.name }}</a
      >
    </td>

    <td v-if="props.activity">
      <PlatformBadge :platform="props.activity.platform" />
    </td>

    <td :title="`${_durationSeconds} seconds`">
      <i class="bi bi-stopwatch"></i> {{ _timeDisplayed }}

      <!-- Share % -->
      <small
        v-if="props.platform || props.game"
        class="mb-0 text-muted"
        :title="
          ((props.platform || props.game!).percent * 100).toFixed(2) +
          '% of all playtime'
        "
      >
        <br />
        {{ ((props.platform || props.game!).percent * 100).toFixed(2) }}%
      </small>
    </td>

    <td v-if="_date && props.showDate" :title="_date.toLocaleString()">
      <i class="bi bi-calendar"></i> {{ _dateDisplayed }}
    </td>

    <td
      v-if="
        (props.platform || props.game) &&
        (props.context === 'platformTable' || props.context === 'gameTable')
      "
    >
      <p>{{ (props.platform || props.game!).totals.user_count }}</p>
    </td>
  </tr>
</template>
