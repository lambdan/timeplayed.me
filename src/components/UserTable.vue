<script setup lang="ts">
import ActivityRow from "./ActivityRow.vue";
import type { Activity, User } from "../models/models";
import UserRow from "./UserRow.vue";

const props = withDefaults(
  defineProps<{ users: User[]; showExpand?: boolean }>(),
  {
    showExpand: false,
  }
);
</script>

<template>
  <table class="table table-hover">
    <thead>
      <tr>
        <th></th>
        <th></th>
        <th>Last active</th>
        <th>Games Played</th>
        <th>Total playtime</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      <UserRow
        v-for="user in users"
        :key="user.id"
        :user="user"
        :showExpand="showExpand"
      />
    </tbody>
  </table>
</template>
