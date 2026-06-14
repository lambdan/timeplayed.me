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
const _game = ref<GameWithStats>();
const _platform = ref<PlatformWithStats>();

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

async function setupUser() {
  if (props.userWithStats) {
    _user.value = props.userWithStats;
    return;
  }
  if (props.activity) {
    await TimeplayedAPI.getUserStats(props.activity.user_id).then((u) => {
      _user.value = u;
    });
    return;
  }
}

async function setupPlatform() {
  if (props.platformWithStats) {
    _platform.value = props.platformWithStats;
    return;
  }
  if (props.activity) {
    await TimeplayedAPI.getPlatformStats(props.activity.platform_id).then(
      (p) => {
        _platform.value = p;
      },
    );
    return;
  }
}

async function setupGame() {
  if (props.gameWithStats) {
    //_game.value = props.game;
    _game.value = await TimeplayedAPI.getGameStats(props.gameWithStats.id);
  } else if (props.activity) {
    _game.value = await TimeplayedAPI.getGameStats(props.activity.game_id);
  }
}

function setupDuration() {
  if (props.durationSeconds) {
    _durationSeconds.value = props.durationSeconds;
  } else if (props.activity) {
    _durationSeconds.value = props.activity.seconds;
  } else if (_game.value) {
    _durationSeconds.value = _game.value.stats.seconds;
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
    return props.activity.game_id;
  }
  if (props.context === "gameTable" && props.gameWithStats) {
    return props.gameWithStats.id;
  }
  return -1;
}

function shouldShowAvatar(): boolean {
  if (!_user.value) {
    return false;
  }
  if (props.userWithStats && props.userWithStats.id) {
    return true;
  }
  if (props.context !== "userPage" && props.activity) {
    return true;
  }
  return false;
}

onMounted(async () => {
  await setupUser();
  await setupPlatform();
  await setupGame();

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
    <td v-if="shouldShowAvatar() && _user">
      <DiscordAvatar :user="_user" :maxWidth="50"></DiscordAvatar>
    </td>

    <td v-if="props.activity && _user && props.context === 'gamePage'">
      <a
        :href="`/user/${props.activity.user_id}`"
        class="link-underline link-underline-opacity-0"
        >{{ _user.name }}</a
      >
    </td>

    <td v-if="props.platformWithStats">
      <PlatformBadge :platform="props.platformWithStats" :showName="false" />
    </td>

    <td v-if="props.platformWithStats">
      <a
        :href="`/platform/${props.platformWithStats.id}`"
        class="link-underline link-underline-opacity-0"
        >{{ props.platformWithStats.display_name }}</a
      >
    </td>

    <td
      v-if="
        _user &&
        (props.context === 'frontPage' ||
          props.context === 'gamePage' ||
          props.context === 'platformPage')
      "
    >
      <a
        :href="`/user/${_user.id}`"
        class="link-underline link-underline-opacity-0"
        >{{ _user.name }}</a
      >
    </td>

    <td v-if="shouldShowGameCover()">
      <GameCover
        :gameId="getGameCoverId()"
        :thumb="true"
        :maxHeight="100"
      ></GameCover>
    </td>

    <td v-if="props.context !== 'gamePage' && props.activity">
      <a
        :href="`/game/${props.activity.game_id}`"
        class="link-underline link-underline-opacity-0"
        >{{ _game ? _game.name : "Loading..." }}</a
      >
    </td>

    <td v-if="gameWithStats">
      <a
        :href="`/game/${gameWithStats.id}`"
        class="link-underline link-underline-opacity-0"
        >{{ gameWithStats.name }}</a
      >
    </td>

    <td v-if="_user && props.context === 'userTable'">
      <a
        :href="`/user/${_user.id}`"
        class="link-underline link-underline-opacity-0"
        >{{ _user.name }}</a
      >
    </td>

    <td
      v-if="props.activity && platformWithStats"
      class="d-none d-md-table-cell"
    >
      <!-- frontpage: show badge (no name) -->
      <PlatformBadge
        v-if="props.context == 'frontPage'"
        :platform="platformWithStats"
        :emulated="props.activity.emulated"
        :showName="false"
        :showAbbreviation="false"
      />

      <!-- any other page (big table): show name -->
      <PlatformBadge
        v-else
        :platform="platformWithStats"
        :emulated="props.activity.emulated"
        :showName="true"
      />
    </td>

    <!-- Duration (always seen) -->
    <td :title="`${_durationSeconds} seconds`" class="p-2 text-nowrap">
      <i class="bi bi-stopwatch"> </i>
      <a
        v-if="props.activity"
        :href="'/activity/' + props.activity.id"
        class="link-underline link-underline-opacity-0"
      >
        {{ _timeDisplayed }}</a
      >
      <span v-else>
        {{ _timeDisplayed }}
      </span>
    </td>

    <!-- Date (hidden on mobile) -->
    <td
      v-if="props.showDate"
      :title="_date?.toString() || 'Never'"
      class="p-2 text-nowrap d-none d-md-table-cell"
    >
      <i class="bi bi-calendar"></i> {{ _dateDisplayed }}
    </td>

    <td v-if="props.showUsers && (platformWithStats || gameWithStats)">
      <p>{{ (platformWithStats || gameWithStats!).stats.user_count || 0 }}</p>
    </td>
  </tr>
</template>
