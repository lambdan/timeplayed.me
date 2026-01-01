<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { getRecapYear, iso8601Date } from "../utils";
import { buildGamesList, buildPlatformsList } from "../utils.stats";
import DiscordAvatar from "../components/DiscordAvatar.vue";
import GameCover from "../components/Games/GameCover.vue";
import type {
  RecapGameEntry,
  RecapPlatformEntry,
} from "../models/stats.models";
import type { Activity, User } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import LoadingBar from "../components/LoadingBar.vue";

const VALID_YEARS = [getRecapYear(), 2025]; // TODO: general solution :D
const available = ref(false);
const route = useRoute();
const loading = ref<boolean>(true);
const loadingProgress = ref(0);
const refYear = ref<number>();
const refUserId = ref<string>();
const activities = ref<Activity[]>([]);
const userInfo = ref<User>();
const gamesList = ref<RecapGameEntry[]>([]);
const platformsList = ref<RecapPlatformEntry[]>([]);
const refLongestSession = ref<Activity>();

const gamesCount = ref(0);
const totalSeconds = ref(0);

const GOLD = "#FFD700";
const SILVER = "#C0C0C0";
const BRONZE = "#CD7F32";

function mostPlayedWeekdays(
  activities: Activity[],
): { day: string; seconds: number; percentage: number }[] {
  const daySeconds: { [key: string]: number } = {
    Sunday: 0,
    Monday: 0,
    Tuesday: 0,
    Wednesday: 0,
    Thursday: 0,
    Friday: 0,
    Saturday: 0,
  };
  let totalSeconds = 0;

  for (const activity of activities) {
    const date = new Date(activity.timestamp);
    const dayName = date.toLocaleDateString("en-US", { weekday: "long" });
    daySeconds[dayName] += activity.seconds;
    totalSeconds += activity.seconds;
  }

  const result = Object.keys(daySeconds).map((day) => ({
    day,
    seconds: daySeconds[day],
    percentage: totalSeconds > 0 ? (daySeconds[day] / totalSeconds) * 100 : 0,
  }));

  result.sort((a, b) => b.seconds - a.seconds);
  return result;
}

function mostPlayedMonths(
  activities: Activity[],
): { month: string; seconds: number; percentage: number }[] {
  const monthSeconds: { [key: string]: number } = {
    January: 0,
    February: 0,
    March: 0,
    April: 0,
    May: 0,
    June: 0,
    July: 0,
    August: 0,
    September: 0,
    October: 0,
    November: 0,
    December: 0,
  };
  let totalSeconds = 0;

  for (const activity of activities) {
    const date = new Date(activity.timestamp);
    const monthName = date.toLocaleDateString("en-US", { month: "long" });
    monthSeconds[monthName] += activity.seconds;
    totalSeconds += activity.seconds;
  }

  const result = Object.keys(monthSeconds).map((month) => ({
    month,
    seconds: monthSeconds[month],
    percentage:
      totalSeconds > 0 ? (monthSeconds[month] / totalSeconds) * 100 : 0,
  }));

  result.sort((a, b) => b.seconds - a.seconds);
  return result;
}

/** How many days in a row the user played something */
function longestStreak(activities: Activity[]): number {
  if (activities.length === 0) {
    return 0;
  }

  // Get unique days the user played something
  const uniqueDays = Array.from(
    new Set(
      activities.map((a) => {
        const d = new Date(a.timestamp);
        // Use UTC to avoid timezone issues
        return `${d.getUTCFullYear()}-${d.getUTCMonth()}-${d.getUTCDate()}`;
      }),
    ),
  ).sort();

  if (uniqueDays.length === 0) {
    return 0;
  }

  let longestStreak = 1;
  let currentStreak = 1;

  for (let i = 1; i < uniqueDays.length; i++) {
    const prev = new Date(uniqueDays[i - 1]);
    const curr = new Date(uniqueDays[i]);
    const diffInTime = curr.getTime() - prev.getTime();
    const diffInDays = diffInTime / (1000 * 3600 * 24);

    if (diffInDays === 1) {
      currentStreak++;
    } else {
      currentStreak = 1;
    }

    if (currentStreak > longestStreak) {
      longestStreak = currentStreak;
    }
  }

  return longestStreak;
}

/** How many days in a row NOTHING was played */
function longestBreak(activities: Activity[]): number {
  if (activities.length === 0) {
    return 0;
  }

  // Sort activities by timestamp
  const sortedActivities = activities
    .slice()
    .sort(
      (a, b) =>
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
    );

  let longestBreak = 0;

  for (let i = 1; i < sortedActivities.length; i++) {
    const prevDate = new Date(sortedActivities[i - 1].timestamp);
    const currentDate = new Date(sortedActivities[i].timestamp);

    // Check the gap between current activity and previous activity
    const diffInTime = currentDate.getTime() - prevDate.getTime();
    const diffInDays = Math.floor(diffInTime / (1000 * 3600 * 24));

    if (diffInDays > longestBreak) {
      longestBreak = diffInDays;
    }
  }

  return longestBreak;
}

/** Most popular game each month */
function mostPopularGameByMonth(activities: Activity[]): {
  [key: string]: string;
} {
  const monthGameMap: { [key: string]: { [gameId: number]: number } } = {};

  for (const activity of activities) {
    const date = new Date(activity.timestamp);
    const month = date.toLocaleString("default", { month: "long" });
    if (!monthGameMap[month]) {
      monthGameMap[month] = {};
    }
    if (!monthGameMap[month][activity.game.id]) {
      monthGameMap[month][activity.game.id] = 0;
    }
    monthGameMap[month][activity.game.id] += activity.seconds;
  }

  const result: { [key: string]: string } = {};
  for (const month in monthGameMap) {
    let topGameId: number | null = null;
    let topSeconds = 0;
    for (const gameId in monthGameMap[month]) {
      if (monthGameMap[month][gameId] > topSeconds) {
        topSeconds = monthGameMap[month][gameId];
        topGameId = parseInt(gameId);
      }
    }
    if (topGameId !== null) {
      const topGame = activities.find((a) => a.game.id === topGameId)?.game;
      if (topGame) {
        result[month] = topGame.name;
      }
    }
  }
  // reverse order to have Jan-Dec
  const orderedMonths = Object.keys(result).sort((a, b) => {
    const monthOrder = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December",
    ];
    return monthOrder.indexOf(a) - monthOrder.indexOf(b);
  });
  const orderedResult: { [key: string]: string } = {};
  for (const month of orderedMonths) {
    orderedResult[month] = result[month];
  }
  return orderedResult;
}

/** Duration played each month */
function durationPlayedByMonth(activities: Activity[]): {
  [key: string]: number;
} {
  const monthDurationMap: { [key: string]: number } = {};

  for (const activity of activities) {
    const date = new Date(activity.timestamp);
    const month = date.toLocaleString("default", { month: "long" });
    if (!monthDurationMap[month]) {
      monthDurationMap[month] = 0;
    }
    monthDurationMap[month] += activity.seconds;
  }

  // reverse order to have Jan-Dec
  const orderedMonths = Object.keys(monthDurationMap).sort((a, b) => {
    const monthOrder = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December",
    ];
    return monthOrder.indexOf(a) - monthOrder.indexOf(b);
  });
  const orderedResult: { [key: string]: number } = {};
  for (const month of orderedMonths) {
    orderedResult[month] = monthDurationMap[month];
  }
  return orderedResult;
}

/** Longest session */
function longestSession(activities: Activity[]): Activity {
  if (activities.length === 0) {
    throw new Error("No activities found");
  }

  let longest = activities[0];

  for (const activity of activities) {
    if (activity.seconds > longest.seconds) {
      longest = activity;
    }
  }

  return longest;
}

/** Most played platform each month */
function mostPlayedPlatformByMonth(activities: Activity[]): {
  [key: string]: string;
} {
  const monthPlatformMap: { [key: string]: { [platform: string]: number } } =
    {};

  for (const activity of activities) {
    const date = new Date(activity.timestamp);
    const month = date.toLocaleString("default", { month: "long" });
    const platform = activity.platform.name || activity.platform.abbreviation;
    if (!monthPlatformMap[month]) {
      monthPlatformMap[month] = {};
    }
    if (!monthPlatformMap[month][platform]) {
      monthPlatformMap[month][platform] = 0;
    }
    monthPlatformMap[month][platform] += activity.seconds;
  }

  const result: { [key: string]: string } = {};
  for (const month in monthPlatformMap) {
    let topPlatform: string | null = null;
    let topSeconds = 0;
    for (const platform in monthPlatformMap[month]) {
      if (monthPlatformMap[month][platform] > topSeconds) {
        topSeconds = monthPlatformMap[month][platform];
        topPlatform = platform;
      }
    }
    if (topPlatform !== null) {
      result[month] = topPlatform;
    }
  }

  // Order months Jan-Dec
  const monthOrder = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];
  const orderedResult: { [key: string]: string } = {};
  for (const month of monthOrder) {
    if (result[month]) {
      orderedResult[month] = result[month];
    }
  }
  return orderedResult;
}

async function _fetchActivities() {
  if (!refUserId.value || !refYear.value) {
    return;
  }
  // UTC dates to avoid timezone issues
  const startDate = new Date(Date.UTC(refYear.value, 0, 1, 0, 0, 0));
  const endDate = new Date(Date.UTC(refYear.value + 1, 0, 1, 0, 0, 0));
  loadingProgress.value = 0;

  while (true) {
    const fetchedActivities = await TimeplayedAPI.getActivities({
      after: startDate.getTime(),
      before: endDate.getTime(),
      limit: 50,
      offset: activities.value.length,
      user: refUserId.value,
    });
    activities.value.push(...fetchedActivities.data);
    loadingProgress.value = Math.min(
      100,
      (activities.value.length / fetchedActivities.total) * 100,
    );
    if (activities.value.length >= fetchedActivities.total) {
      await new Promise((resolve) => setTimeout(resolve, 500)); // small delay to show 100%
      break;
    }
  }

  if (activities.value.length === 0) {
    loadingProgress.value = 100;
    return;
  }

  // fetching done, build lists
  gamesList.value = await buildGamesList(activities.value);
  gamesCount.value = gamesList.value.length;
  totalSeconds.value = activities.value.reduce((sum, a) => sum + a.seconds, 0);
  platformsList.value = await buildPlatformsList(activities.value);
  refLongestSession.value = longestSession(activities.value);
}

onMounted(async () => {
  const userId = route.params.id as string;
  const year = parseInt(route.params.year as string);

  available.value = VALID_YEARS.includes(year);
  if (!available.value) {
    return;
  }

  const data = await TimeplayedAPI.getUser(userId);
  userInfo.value = data.user;
  refUserId.value = userId;
  refYear.value = year;
  await _fetchActivities();
  loading.value = false;
});
</script>

<template>
  <p v-if="!available" class="text-center">Recap not available</p>
  <LoadingBar v-if="available && loading" :percent="loadingProgress" />
  <div v-if="available && !loading" class="container mt-4 mb-4">
    <div class="row mb-3 justify-content-center text-center">
      <DiscordAvatar
        v-if="userInfo"
        :user="userInfo"
        :max-width="300"
        class="mb-3 mx-auto"
      />
      <h1 class="w-100">{{ userInfo?.name }}</h1>
      <h1 class="w-100">Recap for {{ refYear }}</h1>
      <h4>
        Logged <b class="text-warning">{{ activities.length }} sessions</b> for
        a total of
        <b class="text-warning">{{ (totalSeconds / 3600).toFixed(0) }} hours</b>
        across <b class="text-warning">{{ gamesCount }} games</b>
      </h4>
    </div>
    <hr />

    <h1 class="text-center mb-4">Most played games</h1>

    <!-- top 3 row -->
    <div class="row mt-4 mb-4">
      <div
        class="col justify-content-center text-center"
        v-for="(game, idx) in gamesList.slice(0, 3)"
        :key="game.id"
      >
        <div
          class="card h-100 text-center p-2"
          :style="{
            minWidth: 0,
            border:
              idx === 0
                ? '2px solid ' + GOLD
                : idx === 1
                  ? '2px solid ' + SILVER
                  : idx === 2
                    ? '2px solid ' + BRONZE
                    : '',
            boxShadow:
              idx === 0
                ? '0 0 10px ' + GOLD
                : idx === 1
                  ? '0 0 10px ' + SILVER
                  : idx === 2
                    ? '0 0 10px ' + BRONZE
                    : '',
          }"
        >
          <GameCover
            :gameId="game.id"
            :thumb="true"
            :maxWidth="200"
            class="mb-2"
          />
          <h3>
            <a
              :href="`/game/${game.id}`"
              style="color: inherit; text-decoration: none"
            >
              <i
                :style="{
                  color:
                    idx === 0
                      ? GOLD
                      : idx === 1
                        ? SILVER
                        : idx === 2
                          ? BRONZE
                          : 'inherit',
                }"
              >
                {{ game.name }}
              </i>
            </a>
          </h3>
          <h4>{{ (game.seconds / 3600).toFixed(0) }} hours</h4>
          <h5
            class="text-muted"
            :title="
              (game.seconds / 3600 / game.activity_count).toFixed(2) +
              ' hours average session length'
            "
          >
            {{ game.activity_count }} sessions
          </h5>
        </div>
      </div>
    </div>

    <!-- 4-10 row -->
    <div class="row">
      <div
        class="col justify-content-center text-center"
        v-for="(game, idx) in gamesList.slice(3, 10)"
        :key="game.id"
      >
        <div class="card h-100 text-center p-2" style="min-width: 0">
          <GameCover
            :gameId="game.id"
            :thumb="true"
            :maxWidth="100"
            class="mb-2"
          />
          <h5>
            <a
              :href="`/game/${game.id}`"
              style="color: inherit; text-decoration: none"
            >
              <i>{{ game.name }}</i>
            </a>
          </h5>
          <h6>{{ (game.seconds / 3600).toFixed(0) }} hours</h6>

          <h7
            class="text-muted"
            :title="
              (game.seconds / 3600 / game.activity_count).toFixed(2) +
              ' hours average session length'
            "
            >{{ game.activity_count }} sessions</h7
          >
        </div>
      </div>
    </div>

    <hr />

    <div class="row mt-4 mb-4">
      <h2 class="w-100 text-center">Played platforms</h2>
      <p class="text-muted text-center w-100 mb-4">
        (And their most played game)
      </p>
      <div class="row">
        <div
          class="col-6 col-sm-4 col-md-3 col-lg-2 mb-2"
          v-for="(platform, idx) in platformsList"
          :key="platform.name"
        >
          <div
            class="card h-100 text-center p-1"
            :style="{
              minWidth: 0,
              fontSize: '0.9rem',
              border:
                idx === 0
                  ? '2px solid ' + GOLD
                  : idx === 1
                    ? '2px solid ' + SILVER
                    : idx === 2
                      ? '2px solid ' + BRONZE
                      : '',
              boxShadow:
                idx === 0
                  ? '0 0 10px ' + GOLD
                  : idx === 1
                    ? '0 0 10px ' + SILVER
                    : idx === 2
                      ? '0 0 10px ' + BRONZE
                      : '',
            }"
          >
            <div class="card-body p-2">
              <h6
                class="card-title mb-1"
                :style="{
                  fontSize: '1rem',
                  color:
                    idx === 0
                      ? GOLD
                      : idx === 1
                        ? SILVER
                        : idx === 2
                          ? BRONZE
                          : 'inherit',
                }"
              >
                {{ platform.name }}
              </h6>
              <div class="card-text mb-1" style="font-size: 0.95em">
                <b>{{ (platform.seconds / 3600).toFixed(0) }} hours</b>
                <br />
                {{ platform.activity_count }}
                {{ platform.activity_count === 1 ? "session" : "sessions" }}
                <br />
                <span class="text-muted"
                  >({{ platform.percentage.toFixed(0) }}%)</span
                >
              </div>
              <hr class="my-1" />
              <small class="text-muted">{{ platform.most_played_game }}</small>
            </div>
          </div>
        </div>
      </div>
    </div>

    <hr />

    <div class="row mt-4 mb-4">
      <h2 class="mb-4 w-100 text-center">Miscellaneous Stats</h2>
      <!-- 3 columns: Streaks & Session -->
      <div class="col-12 col-md-4 mb-3">
        <div class="card h-100 shadow-sm">
          <div class="card-body text-center">
            <h6 class="card-title mb-2 text-primary">Longest streak</h6>
            <div class="display-6 fw-bold mb-1">
              {{ longestStreak(activities) }} days
            </div>
            <small class="text-muted"
              >Played something this many days in a row</small
            >
          </div>
        </div>
      </div>
      <div class="col-12 col-md-4 mb-3">
        <div class="card h-100 shadow-sm">
          <div class="card-body text-center">
            <h6 class="card-title mb-2 text-danger">Longest break</h6>
            <div class="display-6 fw-bold mb-1">
              {{ longestBreak(activities) }} days
            </div>
            <small class="text-muted"
              >No games played for this many days in a row</small
            >
          </div>
        </div>
      </div>
      <div class="col-12 col-md-4 mb-3" v-if="refLongestSession">
        <div class="card h-100 shadow-sm">
          <div class="card-body text-center">
            <h6 class="card-title mb-2 text-success">Longest session</h6>
            <div class="display-6 fw-bold mb-1">
              {{ (refLongestSession.seconds! / 3600).toFixed(0) }} hours
            </div>
            <small class="text-muted">
              <a :href="'/activity/' + refLongestSession.id"
                ><i>{{ refLongestSession.game.name }}</i> on
                {{ iso8601Date(refLongestSession?.timestamp!) }}</a
              >
            </small>
          </div>
        </div>
      </div>

      <!-- 2 columns: Most played game/platform each month -->
      <div class="col-12 col-md-6 mb-3">
        <div class="card h-100 shadow-sm">
          <div class="card-body">
            <h6 class="card-title mb-3 text-info text-center">
              Most played game each month
            </h6>
            <ul class="list-group list-group-flush">
              <li
                v-for="(game, month) in mostPopularGameByMonth(activities)"
                :key="month"
                class="list-group-item py-1 px-2"
              >
                <span class="float-start fw-bold">{{ month }}</span>
                 
                <span class="float-end">{{ game }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
      <div class="col-12 col-md-6 mb-3">
        <div class="card h-100 shadow-sm">
          <div class="card-body">
            <h6 class="card-title mb-3 text-info text-center">
              Most played platform each month
            </h6>
            <ul class="list-group list-group-flush">
              <li
                v-for="(platform, month) in mostPlayedPlatformByMonth(
                  activities,
                )"
                :key="month"
                class="list-group-item py-1 px-2"
              >
                <span class="fw-bold float-start">{{ month }}</span>
                 
                <span class="float-end">{{ platform }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 2 columns: Most played months / weekdays -->
      <div class="col-12 col-md-6 mb-3">
        <div class="card h-100 shadow-sm">
          <div class="card-body">
            <h6 class="card-title mb-3 text-center">Most played months</h6>
            <ul class="list-group list-group-flush">
              <li
                v-for="(item, idx) in mostPlayedMonths(activities)"
                :key="item.month"
                class="list-group-item py-1 px-2"
              >
                <span
                  class="fw-bold float-start"
                  :style="{
                    color:
                      idx === 0
                        ? GOLD
                        : idx === 1
                          ? SILVER
                          : idx === 2
                            ? BRONZE
                            : 'inherit',
                  }"
                >
                  {{ item.month }}
                </span>
                 
                <span class="float-end"
                  >{{ (item.seconds / 3600).toFixed(0) }} hours ({{
                    item.percentage.toFixed(0)
                  }}%)</span
                >
              </li>
            </ul>
          </div>
        </div>
      </div>
      <div class="col-12 col-md-6 mb-3">
        <div class="card h-100 shadow-sm">
          <div class="card-body">
            <h6 class="card-title mb-3 text-center">Most played weekdays</h6>
            <ul class="list-group list-group-flush">
              <li
                v-for="(day, idx) in mostPlayedWeekdays(activities)"
                :key="day.day"
                class="list-group-item py-1 px-2"
              >
                <span
                  class="fw-bold float-start"
                  :style="{
                    color:
                      idx === 0
                        ? GOLD
                        : idx === 1
                          ? SILVER
                          : idx === 2
                            ? BRONZE
                            : 'inherit',
                  }"
                >
                  {{ day.day }}
                </span>
                 
                <span class="float-end"
                  >{{ (day.seconds / 3600).toFixed(0) }} hours ({{
                    day.percentage.toFixed(0)
                  }}%)</span
                >
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
