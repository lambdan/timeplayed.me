<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { formatDuration, getRecapYear, updateDocumentTitle } from "../utils";
import {
  loadRecap,
  percentChange,
  shortDate,
  type Recap,
} from "../utils.recap";
import type { User } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import DiscordAvatar from "../components/DiscordAvatar.vue";
import LoadingBar from "../components/LoadingBar.vue";
import RecapStatTile from "../components/Recap/RecapStatTile.vue";
import RecapTopGames from "../components/Recap/RecapTopGames.vue";
import RecapCalendar from "../components/Recap/RecapCalendar.vue";
import RecapMonths from "../components/Recap/RecapMonths.vue";
import RecapRhythm from "../components/Recap/RecapRhythm.vue";
import RecapMonthGames from "../components/Recap/RecapMonthGames.vue";
import RecapSessionLengths from "../components/Recap/RecapSessionLengths.vue";
import RecapPlatforms from "../components/Recap/RecapPlatforms.vue";

const route = useRoute();
const year = parseInt(route.params.year as string);
const userId = parseInt(route.params.id as string);

// past years, and the current year once it's recap season
const available =
  (year >= 2025 && year < new Date().getFullYear()) || year === getRecapYear();
const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

const progress = ref(0);
const failed = ref(false);
const user = ref<User>();
const recap = ref<Recap>();

const gameNames = computed(
  () => new Map(recap.value?.games.map((g) => [g.game_id, g.name])),
);
const platformNames = computed(
  () => new Map(recap.value?.platforms.map((p) => [p.platform_id, p.name])),
);
const totals = computed(() => recap.value!.totals);
const prev = computed(() => recap.value!.previous_year);

const oldestGame = computed(() =>
  recap
    .value!.games.filter((g) => g.release_year)
    // most played first, and sort is stable, so ties go to the most played one
    .sort((a, b) => a.release_year! - b.release_year!)
    .at(0),
);

onMounted(async () => {
  updateDocumentTitle(`${year} Recap`);
  if (!available) return;
  try {
    const [u, r] = await Promise.all([
      TimeplayedAPI.getUser(userId),
      loadRecap(userId, year, (p) => (progress.value = p)),
    ]);
    user.value = u;
    recap.value = r;
    updateDocumentTitle(`${u.name} - ${year} Recap`);
  } catch (e) {
    console.error(e);
    failed.value = true;
  }
});
</script>

<template>
  <!-- container-xl, the global css breaks .container on small screens -->
  <div class="container-xl px-0 mt-4 mb-5">
    <p v-if="!available" class="text-center my-5">Recap not available</p>
    <p v-else-if="failed" class="text-center my-5">Couldn't load the recap</p>
    <LoadingBar v-else-if="!recap || !user" :percent="progress" />

    <template v-else>
      <header class="d-flex align-items-center gap-3 flex-wrap">
        <DiscordAvatar :user="user" :max-width="72" />
        <div>
          <div class="small text-body-secondary">{{ user.name }}</div>
          <h1 class="fw-bold mb-0">{{ year }} recap</h1>
        </div>
      </header>

      <p v-if="!totals.sessions" class="text-body-secondary my-5">
        No activity in {{ year }}
      </p>

      <template v-else>
        <div class="row row-cols-2 row-cols-md-3 row-cols-lg-5 g-3 mt-2">
          <div class="col">
            <RecapStatTile
              label="Playtime"
              :value="formatDuration(totals.seconds)"
              :sub="`${formatDuration(totals.seconds / recap.days.length)} per day`"
              :change="percentChange(totals.seconds, prev?.seconds)"
              :previousYear="year - 1"
            />
          </div>
          <div class="col">
            <RecapStatTile
              label="Sessions"
              :value="`${totals.sessions}`"
              :sub="`${formatDuration(totals.seconds / totals.sessions)} average`"
              :change="percentChange(totals.sessions, prev?.sessions)"
              :previousYear="year - 1"
            />
          </div>
          <div class="col">
            <RecapStatTile
              label="Games"
              :value="`${totals.games}`"
              :sub="
                prev
                  ? `${totals.new_games} played for the first time`
                  : undefined
              "
              :change="percentChange(totals.games, prev?.games)"
              :previousYear="year - 1"
            />
          </div>
          <div class="col">
            <RecapStatTile
              label="Days played"
              :value="`${totals.days_played}`"
              :sub="`of ${recap.days.length} (${((totals.days_played / recap.days.length) * 100).toFixed(0)}%)`"
            />
          </div>
          <div class="col" v-if="recap.community">
            <RecapStatTile
              label="Share of all playtime"
              :value="`${recap.community.share.toFixed(recap.community.share < 10 ? 1 : 0)}%`"
              :sub="`#${recap.community.rank} of ${recap.community.players} players`"
            />
          </div>
        </div>

        <section class="mt-5">
          <h2 class="h4 fw-bold mb-3">Games</h2>
          <RecapTopGames :games="recap.games" :showNew="!!prev" />
        </section>

        <section class="mt-5">
          <h2 class="h4 fw-bold mb-3">Activity</h2>
          <RecapCalendar
            :days="recap.days"
            :sessionsByDay="recap.sessionsByDay"
            :year="year"
            :gameNames="gameNames"
            :platformNames="platformNames"
          />
          <div class="row g-3 mt-1">
            <div class="col-12 col-md-4" v-if="recap.longest_streak">
              <RecapStatTile
                label="Longest streak"
                :value="`${recap.longest_streak.days} days`"
                :sub="`${shortDate(recap.longest_streak.start)} – ${shortDate(recap.longest_streak.end)}`"
              />
            </div>
            <div class="col-12 col-md-4" v-if="recap.longest_break">
              <RecapStatTile
                label="Longest break"
                :value="`${recap.longest_break.days} days`"
                :sub="`${shortDate(recap.longest_break.start)} – ${shortDate(recap.longest_break.end)}`"
              />
            </div>
            <div class="col-12 col-md-4" v-if="recap.biggest_day">
              <RecapStatTile
                label="Most played day"
                :value="formatDuration(recap.biggest_day.seconds)"
                :sub="`${shortDate(recap.biggest_day.date)} · ${gameNames.get(recap.biggest_day.top_game_id)}`"
              />
            </div>
          </div>
        </section>

        <section class="mt-5">
          <h2 class="h4 fw-bold mb-3">Months</h2>
          <RecapMonthGames
            :sessionsByDay="recap.sessionsByDay"
            :games="recap.games"
            :year="year"
          />
          <RecapMonths
            class="mt-3"
            :months="recap.months"
            :gameNames="gameNames"
          />
        </section>

        <section class="mt-5">
          <h2 class="h4 fw-bold mb-3">Time of day</h2>
          <p class="small text-body-secondary">Times in {{ timezone }}</p>
          <RecapRhythm
            :weekdays="recap.weekdays"
            :hours="recap.hours"
            :weekHours="recap.weekHours"
          />
        </section>

        <section class="mt-5">
          <h2 class="h4 fw-bold mb-3">Platforms</h2>
          <RecapPlatforms :platforms="recap.platforms" :gameNames="gameNames" />
        </section>

        <section class="mt-5">
          <h2 class="h4 fw-bold mb-3">Session length</h2>
          <RecapSessionLengths :sessions="recap.sessionsByDay.flat()" />
        </section>

        <section class="mt-5">
          <h2 class="h4 fw-bold mb-3">Other</h2>
          <div class="row g-3">
            <div class="col-12 col-md-4" v-if="recap.longest_session">
              <RecapStatTile
                label="Longest session"
                :value="formatDuration(recap.longest_session.seconds)"
              >
                <a
                  :href="`/activity/${recap.longest_session.activity_id}`"
                  class="link-body-emphasis text-decoration-none"
                  >{{ gameNames.get(recap.longest_session.game_id) }}</a
                >
                · {{ shortDate(recap.longest_session.date) }}
              </RecapStatTile>
            </div>
            <div class="col-12 col-md-4" v-if="oldestGame">
              <RecapStatTile
                label="Oldest game"
                :value="`${oldestGame.release_year}`"
              >
                <a
                  :href="`/game/${oldestGame.game_id}`"
                  class="link-body-emphasis text-decoration-none"
                  >{{ oldestGame.name }}</a
                >
                · {{ formatDuration(oldestGame.seconds) }}
              </RecapStatTile>
            </div>
            <div class="col-12 col-md-4">
              <RecapStatTile
                :label="`Released in ${year}`"
                :value="`${recap.games.filter((g) => g.release_year === year).length}`"
                :sub="`of ${totals.games} games played`"
              />
            </div>
          </div>
        </section>
      </template>
    </template>
  </div>
</template>
