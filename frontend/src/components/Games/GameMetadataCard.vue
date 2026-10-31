<script setup lang="ts">
import type { Game } from "../../api.models";
import CalendarBasic from "../CalendarBasic.vue";

defineProps<{ game: Game }>();
</script>

<template>
  <div class="card p-0">
    <h2 class="card-header">Metadata</h2>
    <div class="card-body">
      <table class="table table-sm table-hover mb-0">
        <tbody>
          <tr>
            <th class="text-nowrap">ID</th>
            <td>{{ game.id }}</td>
          </tr>
          <tr v-if="game.igdb_id">
            <th class="text-nowrap">IGDB</th>
            <td>{{ game.igdb_id }}</td>
          </tr>
          <tr v-if="game.steam_id">
            <th class="text-nowrap">Steam</th>
            <td>
              <a
                :href="'https://store.steampowered.com/app/' + game.steam_id"
                >{{ game.steam_id }}</a
              >
            </td>
          </tr>
          <tr v-if="game.sgdb_id">
            <th class="text-nowrap">SteamGridDB</th>
            <td>
              <a :href="'https://www.steamgriddb.com/game/' + game.sgdb_id">{{
                game.sgdb_id
              }}</a>
            </td>
          </tr>
          <tr v-if="game.aliases.length > 0">
            <th class="text-nowrap">Aliases</th>
            <td class="text-break">
              <div v-for="alias in game.aliases" :key="alias">{{ alias }}</div>
            </td>
          </tr>
          <tr>
            <th class="text-nowrap">Created</th>
            <td>
              <CalendarBasic
                :date="game.created"
                :showIcon="false"
                :absolute="true"
              />
            </td>
          </tr>
          <tr>
            <th class="text-nowrap">Updated</th>
            <td>
              <CalendarBasic
                :date="game.updated"
                :showIcon="false"
                :absolute="true"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
