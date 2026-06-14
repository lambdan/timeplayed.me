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
  game?: GameWithStats;
  user?: UserWithStats;
  platform?: PlatformWithStats;
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
  if (props.user) {
    _user.value = props.user;
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
  if (props.platform) {
    _platform.value = props.platform;
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
  if (props.game) {
    //_game.value = props.game;
    _game.value = await TimeplayedAPI.getGameStats(props.game.id);
  } else if (props.activity) {
    _game.value = await TimeplayedAPI.getGameStats(props.activity.game_id);
  }
}

function setupDuration() {
  if (props.durationSeconds) {
    console.log("Setting up duration with props:", props);
    _durationSeconds.value = props.durationSeconds;
  } else if (props.activity) {
    console.log("Setting up duration from activity:", props.activity);
    _durationSeconds.value = props.activity.seconds;
  } else if (_game.value) {
    console.log("Setting up duration from game stats:", _game.value.stats);
    _durationSeconds.value = _game.value.stats.seconds;
  } else {
    throw new Error("Either activity or duration prop must be provided");
  }
  console.log("Duration seconds:", _durationSeconds.value);
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
  if (props.context === "gameTable" && props.game) {
    return props.game.id;
  }
  return -1;
}

function shouldShowAvatar(): boolean {
  if (props.user && props.user.id) {
    return true;
  }
  if (props.context !== "userPage" && props.activity) {
    return true;
  }
  return false;
}

function getUserForDiscordAvatar(): User {
  if (_user.value) {
    return _user.value;
  }
  throw new Error("No user available for Discord avatar");
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

  if (props.context && showOnContexts.includes(props.context) && props.user) {
    _date.value = props.user.stats.last_activity
      ? new Date(props.user.stats.last_activity)
      : undefined;
    updateDate(_date.value!);
  }

  if (props.activity) {
    _id.value = props.activity.id;
    setupActivity(props.activity);
  } else if (props.user) {
    _id.value = props.user.id;
  } else if (props.game) {
    _id.value = props.game.id;
  } else if (props.platform) {
    _id.value = props.platform.id;
  }

  setupDuration();
});
</script>

<template>
  <tr class="align-middle" :key="_id">
    <!--<td v-if="props.activity" class="d-none d-md-table-cell">
      <small title="Activity ID" class="text-secondary">
        <a
          :href="'/activity/' + props.activity.id"
          class="link-secondary link-underline link-underline-opacity-0"
          >{{ props.activity.id }}</a
        ></small
      >
    </td>-->

    <td v-if="shouldShowAvatar()">
      <DiscordAvatar
        :user="getUserForDiscordAvatar()"
        :maxWidth="50"
      ></DiscordAvatar>
    </td>

    <td v-if="props.activity && _user && props.context === 'gamePage'">
      <a
        :href="`/user/${props.activity.user_id}`"
        class="link-underline link-underline-opacity-0"
        >{{ _user.name }}</a
      >
    </td>

    <td v-if="props.platform">
      <PlatformBadge :platform="props.platform" :showName="false" />
    </td>

    <td v-if="props.platform">
      <a
        :href="`/platform/${props.platform.id}`"
        class="link-underline link-underline-opacity-0"
        >{{ props.platform.display_name }}</a
      >
    </td>

    <td
      v-if="
        props.user &&
        (props.context === 'frontPage' ||
          props.context === 'gamePage' ||
          props.context === 'platformPage')
      "
    >
      <a
        :href="`/user/${props.user.id}`"
        class="link-underline link-underline-opacity-0"
        >{{ props.user.name }}</a
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
        >{{ game ? game.name : "Loading..." }}</a
      >
    </td>

    <td v-if="game">
      <a
        :href="`/game/${game.id}`"
        class="link-underline link-underline-opacity-0"
        >{{ game.name }}</a
      >
    </td>

    <td v-if="props.user && props.context === 'userTable'">
      <a
        :href="`/user/${props.user.id}`"
        class="link-underline link-underline-opacity-0"
        >{{ props.user.name }}</a
      >
    </td>

    <td v-if="props.activity && platform" class="d-none d-md-table-cell">
      <!-- frontpage: show badge (no name) -->
      <PlatformBadge
        v-if="props.context == 'frontPage'"
        :platform="platform"
        :emulated="props.activity.emulated"
        :showName="false"
        :showAbbreviation="false"
      />

      <!-- any other page (big table): show name -->
      <PlatformBadge
        v-else
        :platform="platform"
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

    <td v-if="props.showUsers && (platform || game)">
      <p>{{ (platform || game!).stats.user_count || 0 }}</p>
    </td>
  </tr>
</template>
