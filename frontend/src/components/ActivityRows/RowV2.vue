<script setup lang="ts">
import { onMounted, ref } from "vue";
import { formatDuration, timeAgo } from "../../utils";
import DiscordAvatar from "../DiscordAvatar.vue";
import GameCover from "../Games/GameCover.vue";
import PlatformBadge from "../Badges/PlatformBadge.vue";
import CalendarBasic from "../CalendarBasic.vue";
import type {
  Activity,
  Game,
  GameWithStats,
  Platform,
  PlatformWithStats,
  User,
  UserWithStats,
} from "../../api.models";
import { TimeplayedAPI } from "../../api.client";

const props = defineProps<{
  activity?: Activity;
  gameWithStats?: GameWithStats;
  userWithStats?: UserWithStats;
  platformWithStats?: PlatformWithStats;
  durationSeconds?: number;
  showDate?: boolean;
  date?: Date;
  showUsers: boolean;
  context?:
    | "gamePage"
    | "platformPage"
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

const _user = ref<User>();
const _userWithStats = ref<UserWithStats>();
const _game = ref<Game>();
const _gameWithStats = ref<GameWithStats>();
const _platform = ref<Platform>();
const _platformWithStats = ref<PlatformWithStats>();

function updateDate(d: Date | undefined) {
  if (d) {
    _dateDisplayed.value = timeAgo(d, true);
  } else {
    _dateDisplayed.value = "Never";
  }
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
  } else if (_gameWithStats.value) {
    _durationSeconds.value = _gameWithStats.value.stats.seconds;
  } else {
    throw new Error("Either activity or duration prop must be provided");
  }
  _timeDisplayed.value = formatDuration(_durationSeconds.value);
}

/** Returns -1 if game cover should not be shown */
function getGameCoverId(): number {
  if (props.context === "userPage" && props.activity) {
    return props.activity.game_id;
  }
  if (props.context === "gameTable" && props.gameWithStats) {
    return props.gameWithStats.id;
  }
  return -1;
}

onMounted(async () => {
  // user
  if (props.userWithStats) {
    _userWithStats.value = props.userWithStats;
    _user.value = props.userWithStats;
  } else if (props.activity) {
    _user.value = await TimeplayedAPI.getUser(props.activity.user_id);
  }
  // game
  if (props.gameWithStats) {
    _gameWithStats.value = props.gameWithStats;
    _game.value = props.gameWithStats;
  } else if (props.activity) {
    _game.value = await TimeplayedAPI.getGame(props.activity.game_id);
  }
  // platform
  if (props.platformWithStats) {
    _platformWithStats.value = props.platformWithStats;
    _platform.value = props.platformWithStats;
  } else if (props.activity) {
    _platform.value = await TimeplayedAPI.getPlatform(
      props.activity.platform_id,
    );
  }

  _date.value = props.date;

  updateDate(props.date);

  const showOnContexts = [
    "userPage",
    "platformPage",
    "platformTable",
    "gameTable",
  ];

  if (
    props.context &&
    showOnContexts.includes(props.context) &&
    props.userWithStats
  ) {
    _date.value = props.userWithStats.stats.last_activity
      ? new Date(props.userWithStats.stats.last_activity)
      : undefined;
    updateDate(_date.value!);
  }

  if (props.activity) {
    _id.value = props.activity.id;
    setupActivity(props.activity);
  } else if (props.userWithStats) {
    _id.value = props.userWithStats.id;
  } else if (props.gameWithStats) {
    _id.value = props.gameWithStats.id;
  } else if (props.platformWithStats) {
    _id.value = props.platformWithStats.id;
  }

  setupDuration();
});
</script>

<template>
  <tr class="align-middle" :key="_id">
    <!-- always show user avatar, except on users own page  -->
    <td v-if="_user && props.context !== 'userPage'">
      <DiscordAvatar :user="_user" :maxWidth="50"></DiscordAvatar>
    </td>

    <!-- always show user, except if its an activity row -->
    <td v-if="_user && !activity">
      <a
        :href="`/user/${_user.id}`"
        class="link-underline link-underline-opacity-0"
        >{{ _user.display_name }}</a
      >
    </td>

    <!-- show game cover everywhere, except frontpage and game page -->
    <!-- and hidden on mobile -->
    <td
      v-if="
        _game && props.context !== 'frontPage' && props.context !== 'gamePage'
      "
    >
      <GameCover
        :gameId="_game.id"
        :thumb="true"
        :maxHeight="100"
        class="d-none d-md-table-cell"
      ></GameCover>
    </td>

    <!-- always show game, except on game pages -->
    <td v-if="_game && props.context !== 'gamePage'">
      <a
        :href="`/game/${_game.id}`"
        class="link-underline link-underline-opacity-0"
        >{{ _game.name }}</a
      >
    </td>

    <td v-if="_platform && props.context !== 'platformPage'">
      <PlatformBadge :platform="_platform" :showName="false" />
    </td>

    <td v-if="_platform && props.context === 'platformTable'">
      <a
        :href="`/platform/${_platform.id}`"
        class="link-underline link-underline-opacity-0"
        >{{ _platform.display_name }}</a
      >
    </td>

    <!-- Duration (always seen) -->
    <td :title="`${_durationSeconds} seconds`" class="p-2 text-nowrap">
      <i class="bi bi-stopwatch"> </i>
      <a
        v-if="props.activity"
        :href="'/activity/' + props.activity.id"
        class="link-underline link-underline-opacity-0"
      >
        {{ _timeDisplayed || "-" }}</a
      >
      <span v-else>
        {{ _timeDisplayed || "-" }}
      </span>
    </td>

    <!-- Date (hidden on mobile) -->
    <td v-if="props.showDate" class="p-2 text-nowrap d-none d-md-table-cell">
      <CalendarBasic :date="_date" :absolute="false" />
    </td>

    <td v-if="props.showUsers && (platformWithStats || gameWithStats)">
      <p>{{ (platformWithStats || gameWithStats!).stats.user_count || 0 }}</p>
    </td>
  </tr>
</template>
