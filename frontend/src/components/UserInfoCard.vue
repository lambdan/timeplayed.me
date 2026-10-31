<script setup lang="ts">
import { formatDuration, getRecapYear } from "../utils";
import DiscordAvatar from "./DiscordAvatar.vue";
import type { UserWithStats } from "../api.models";
import CalendarBasic from "./CalendarBasic.vue";
import PlatformBadge from "./Badges/PlatformBadge.vue";
import { useLookups } from "../composables/useLookups";

defineProps<{ user: UserWithStats }>();

const lookups = useLookups();

const recapYear = getRecapYear();
</script>

<template>
  <div class="card p-0">
    <h1 class="card-header d-flex align-items-center gap-2">
      <span class="me-auto">{{ user.display_name }}</span>
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
          <table class="table table-sm table-hover mb-0">
            <tbody>
              <!-- the display name is in the header already -->
              <tr v-if="user.name !== user.display_name">
                <th class="text-nowrap">Username</th>
                <td class="text-break">{{ user.name }}</td>
              </tr>
              <tr>
                <th class="text-nowrap">Playtime</th>
                <td>{{ formatDuration(user.stats.seconds) }}</td>
              </tr>
              <tr>
                <th class="text-nowrap">Activities</th>
                <td>{{ user.stats.activity_count }}</td>
              </tr>
              <tr v-if="user.stats.activity_count > 0">
                <th class="text-nowrap">Average session</th>
                <td>
                  {{
                    formatDuration(
                      user.stats.seconds / user.stats.activity_count,
                    )
                  }}
                </td>
              </tr>
              <tr>
                <th class="text-nowrap">Games</th>
                <td>{{ user.stats.game_count }}</td>
              </tr>
              <tr>
                <th class="text-nowrap">Platforms</th>
                <td>{{ user.stats.platform_count }}</td>
              </tr>
              <tr v-if="lookups.platform(user.default_platform_id)">
                <th class="text-nowrap">Default platform</th>
                <td>
                  <PlatformBadge
                    :platform="lookups.platform(user.default_platform_id)!"
                  />
                </td>
              </tr>
              <tr v-if="user.stats.first_activity">
                <th class="text-nowrap">First played</th>
                <td>
                  <CalendarBasic
                    :date="user.stats.first_activity"
                    :absolute="true"
                    :showIcon="false"
                  />
                </td>
              </tr>
              <tr v-if="user.stats.last_activity">
                <th class="text-nowrap">Last played</th>
                <td>
                  <CalendarBasic
                    :date="user.stats.last_activity"
                    :absolute="true"
                    :showIcon="false"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
