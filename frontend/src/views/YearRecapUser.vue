<script setup lang="ts">
import { onMounted, ref } from "vue";
import { User, type Activity, type API_Activities, type UserWithStats } from "../models/models";
import { useRoute } from "vue-router";
import { fetchActivities, fetchUserInfo, iso8601Date } from "../utils";
import { RecapPlatformEntry, type RecapGameEntry } from "../models/stats.models";
import { buildGamesList, buildPlatformsList } from "../utils.stats";
import DiscordAvatar from "../components/DiscordAvatar.vue";
import type DiscordAvatarVue from "../components/DiscordAvatar.vue";
import GameCover from "../components/Games/GameCover.vue";

const route = useRoute();
const loading = ref<boolean>(true);
const loadingProgress = ref(0);
const refYear = ref<number>();
const refUserId = ref<string>();
const activities = ref<Activity[]>([]);
const userInfo = ref<User>();
const gamesList = ref<RecapGameEntry[]>([]);
const platformsList = ref<RecapPlatformEntry[]>([]);

const gamesCount = ref(0);
const totalSeconds = ref(0);

const GOLD = "#FFD700";
const SILVER = "#C0C0C0";
const BRONZE = "#CD7F32";

function mostPlayedWeekdays(activities: Activity[]): { day: string; seconds: number; percentage: number }[] {
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

/** How many days in a row the user played something */
function longestStreak(activities: Activity[]): number {
  if (activities.length === 0) {
    return 0;
  }

  // Sort activities by timestamp
  const sortedActivities = activities.slice().sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  let longestStreak = 1;
  let currentStreak = 1;

  for (let i = 1; i < sortedActivities.length; i++) {
    const prevDate = new Date(sortedActivities[i - 1].timestamp);
    const currentDate = new Date(sortedActivities[i].timestamp);

    // Check if current activity is the next day after the previous activity
    const diffInTime = currentDate.getTime() - prevDate.getTime();
    const diffInDays = diffInTime / (1000 * 3600 * 24);

    if (diffInDays === 1) {
      currentStreak++;
    } else if (diffInDays > 1) {
      currentStreak = 1; // Reset streak
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
  const sortedActivities = activities.slice().sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

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
function mostPopularGameByMonth(activities: Activity[]): { [key: string]: string } {
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
      const topGame = activities.find(a => a.game.id === topGameId)?.game;
      if (topGame) {
        result[month] = topGame.name;
      }
    }
  }
  // reverse order to have Jan-Dec
  const orderedMonths = Object.keys(result).sort((a, b) => {
    const monthOrder = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    return monthOrder.indexOf(a) - monthOrder.indexOf(b);
  });
  const orderedResult: { [key: string]: string } = {};
  for (const month of orderedMonths) {
    orderedResult[month] = result[month];
  }
  return orderedResult;
}

/** Duration played each month */
function durationPlayedByMonth(activities: Activity[]): { [key: string]: number } {
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
    const monthOrder = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    return monthOrder.indexOf(a) - monthOrder.indexOf(b);
  });
  const orderedResult: { [key: string]: number } = {};
  for (const month of orderedMonths) {
    orderedResult[month] = monthDurationMap[month];
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

  while(true) {
    const fetchedActivities = await fetchActivities({
      userId: refUserId.value + "",
      after: startDate,
      before: endDate,
      limit: 500,
      offset: activities.value.length,
    });
    activities.value.push(...fetchedActivities.data);
    loadingProgress.value = Math.min(100, (activities.value.length / fetchedActivities._total) * 100);
    if (activities.value.length >= fetchedActivities._total) {
      break;
    }
  }

  // fetching done, build lists
  gamesList.value = await buildGamesList(activities.value);
  gamesCount.value = gamesList.value.length;
  totalSeconds.value = activities.value.reduce((sum, a) => sum + a.seconds, 0);
  platformsList.value = await buildPlatformsList(activities.value);
}

onMounted(async () => {
  const userId = route.params.id as string;
  const year = parseInt(route.params.year as string);
  userInfo.value = await fetchUserInfo(userId);
  refUserId.value = userId;
  refYear.value = year;
  await _fetchActivities();
  loading.value = false;
});
</script>

<template>
  <div v-if="loading">Loading... {{ Math.round(loadingProgress) }}%</div>
  <div v-else>
    <div class="row mb-3 justify-content-center text-center">
      <DiscordAvatar v-if="userInfo" :user="userInfo" :max-width="300" class="mb-3 mx-auto" />
      <h1 class="w-100">{{ userInfo?.name }}</h1>
      <h1 class="w-100">Recap for {{ refYear }}</h1>
      <h4>
        Played a total of <b class="text-warning">{{ (totalSeconds / 3600).toFixed(0) }} hours</b> over <b class="text-warning">{{ gamesCount }} games</b> in <b class="text-warning">{{ refYear }}</b>
      </h4>
    </div>
    <hr>

    <h1 class="text-center mb-4">Most played games</h1>

    <!-- top 3 row -->
    <div class="row mb-4">
      <div
      class="col justify-content-center text-center"
      v-for="(game, idx) in gamesList.slice(0,3)"
      :key="game.id"
      >
      <div
        class="card h-100 text-center p-2"
        :style="{
        minWidth: 0,
        border: idx === 0 ? '2px solid ' + GOLD :
             idx === 1 ? '2px solid ' + SILVER :
             idx === 2 ? '2px solid ' + BRONZE : '',
        boxShadow: idx === 0 ? '0 0 10px ' + GOLD :
              idx === 1 ? '0 0 10px ' + SILVER :
              idx === 2 ? '0 0 10px ' + BRONZE : ''
        }"
      >
        <GameCover :game="{ id: game.id, name: game.name }" :thumb="true" :maxWidth="200" class="mb-2" />
        <h3>
        <a :href="`/game/${game.id}`" style="color: inherit; text-decoration: none;">
          <i :style="{
          color: idx === 0 ? GOLD :
               idx === 1 ? SILVER :
               idx === 2 ? BRONZE : 'inherit'
          }">
          {{ game.name }}
          </i>
        </a>
        </h3>
        <h4>{{ (game.seconds / 3600).toFixed(0) }} hours</h4>
      </div>
      </div>
    </div>

    <!-- 4-10 row -->
    <div class="row">
      <div
      class="col justify-content-center text-center"
      v-for="(game, idx) in gamesList.slice(3,10)"
      :key="game.id"
      >
      <div class="card h-100 text-center p-2" style="min-width: 0;">
        <GameCover :game="{ id: game.id, name: game.name }" :thumb="true" :maxWidth="100" class="mb-2" />
        <h5>
        <a :href="`/game/${game.id}`" style="color: inherit; text-decoration: none;">
          <i>{{ game.name }}</i>
        </a>
        </h5>
        <h6>{{ (game.seconds / 3600).toFixed(0) }} hours</h6>
      </div>
      </div>
    </div>

    <hr>
    

    <div class="row">
      <h2>Played platforms</h2>
      <p class="text-muted">And their most played game</p>
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
          border: idx === 0 ? '2px solid ' + GOLD :
             idx === 1 ? '2px solid ' + SILVER :
             idx === 2 ? '2px solid ' + BRONZE : '',
          boxShadow: idx === 0 ? '0 0 10px ' + GOLD :
              idx === 1 ? '0 0 10px ' + SILVER :
              idx === 2 ? '0 0 10px ' + BRONZE : ''
        }"
        >
        <div class="card-body p-2">
          <h6
          class="card-title mb-1"
          :style="{
            fontSize: '1rem',
            color: idx === 0 ? GOLD :
               idx === 1 ? SILVER :
               idx === 2 ? BRONZE : 'inherit'
          }"
          >
          {{ platform.name }}
          </h6>
          <div class="card-text mb-1" style="font-size: 0.95em;">
          <b>{{ (platform.seconds / 3600).toFixed(0) }} hours</b>
          <br>
          <span class="text-muted">({{ platform.percentage.toFixed(0) }}%)</span>
          </div>
          <hr class="my-1">
          <small class="text-muted">{{ platform.most_played_game }}</small>
        </div>
        </div>
      </div>
      </div>
    </div>

    <hr>
    <div class="row">
      <div class="col">
        <h2>Most played game each month</h2>
        <ul>
          <li v-for="(game, month) in mostPopularGameByMonth(activities)" :key="month">
            <b>{{ month }}</b> - {{ game }}
          </li>
        </ul>
      </div>

      <div class="col">
        <h2>Most played months</h2>
        <ul>
          <li
        v-for="(item, idx) in Object.entries(durationPlayedByMonth(activities)).sort((a, b) => b[1] - a[1])"
        :key="item[0]"
          >
        <b :style="{
          color: idx === 0 ? GOLD :
             idx === 1 ? SILVER :
             idx === 2 ? BRONZE : 'inherit'
        }">
          {{ item[0] }}
        </b>
        - {{ (item[1] / 3600).toFixed(0) }} hours
          </li>
        </ul>
      </div>

      <div class="col">
        <h2>Most played weekdays</h2>
        <ul>
          <li
        v-for="(day, idx) in mostPlayedWeekdays(activities)"
        :key="day.day"
          >
        <b :style="{
          color: idx === 0 ? GOLD :
             idx === 1 ? SILVER :
             idx === 2 ? BRONZE : 'inherit'
        }">
          {{ day.day }}
        </b>
        - {{ (day.seconds / 3600).toFixed(0) }} hours ({{ day.percentage.toFixed(0) }}%)
          </li>
        </ul>
      </div>

      <div class="col">
        <h2>Misc</h2>
        <h5>Longest streak: <b>{{ longestStreak(activities) }} days</b></h5>
        <p class="text-muted">Something was played this many days in a row</p>
        <h5>Longest break: <b>{{ longestBreak(activities) }} days</b></h5>
        <p class="text-muted">Nothing was played this many days in a row</p>
      </div>
    </div>
  </div>

</template>