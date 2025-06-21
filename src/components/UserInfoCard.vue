<script setup lang="ts">
import type { User } from "../models/models";

const FALLBACK_AVATAR = "https://cdn.discordapp.com/embed/avatars/0.png";

defineProps<{ user: User }>();
</script>

<template>
  <div class="card">
    <h1 class="card-header">{{ user.name }}</h1>
    <div class="card-body">
      <div class="row">
        <div class="col-lg-2 mb-4">
          <img
            :src="user.avatar_url ?? FALLBACK_AVATAR"
            class="img-thumbnail img-fluid rounded-circle"
          />
        </div>

        <div class="col mb-4">
          <table class="table table-responsive table-hover">
            <tbody>
              <tr>
                <td><b>Discord ID:</b></td>
                <td>{{ user.id }}</td>
              </tr>
              <tr>
                <td><b>First session:</b></td>
                <td>Mon, 20 Jan 2025 19:11:26 GMT</td>
              </tr>
              <tr>
                <td><b>Last active:</b></td>
                <td>Sat, 21 Jun 2025 12:09:58 GMT</td>
              </tr>
              <tr>
                <td><b>Active days:</b></td>
                <td>139</td>
              </tr>
              <tr>
                <td><b>Longest streak:</b></td>
                <td>31</td>
              </tr>
              <tr>
                <td><b>Longest break:</b></td>
                <td>3 days</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="col mb-4">
          <table class="table table-responsive table-hover">
            <tbody>
              <tr>
                <td><b>Games played:</b></td>
                <td>48</td>
              </tr>
              <tr>
                <td><b>Total playtime:</b></td>
                <td>361.5 hours</td>
              </tr>
              <tr>
                <td><b>Average playtime/game:</b></td>
                <td>7.5 hours</td>
              </tr>
              <tr>
                <td><b>Total sessions:</b></td>
                <td><a href="/user/84733730387673088/sessions">451</a></td>
              </tr>
              <tr>
                <td><b>Average sessions/game:</b></td>
                <td>9</td>
              </tr>
              <tr>
                <td><b>Average session length:</b></td>
                <td>48 minutes</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
