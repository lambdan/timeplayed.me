<script setup lang="ts">
import { ref, watch } from "vue";
import type { User } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import { useApiToken } from "../composables/useApiToken";

const { token, clearApiToken } = useApiToken();
const sessionUser = ref<User>();

async function refreshSessionUser() {
  if (!token.value) {
    sessionUser.value = undefined;
    return;
  }

  try {
    sessionUser.value = await TimeplayedAPI.whoAmI(token.value);
  } catch (err) {
    sessionUser.value = undefined;
  }
}

function logoutSession() {
  clearApiToken();
  sessionUser.value = undefined;
}

watch(token, () => {
  refreshSessionUser();
}, { immediate: true });
</script>

<template>
  <nav class="navbar navbar-expand-lg">
    <div class="container">
      <a href="/" class="navbar-brand">timeplayed.me</a>
      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarSupportedContent"
        aria-controls="navbarSupportedContent"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="navbarSupportedContent">
        <ul class="navbar-nav gap-2">
          <li class="nav-item">
            <a class="nav-link" href="/">
              <i class="bi bi-house-fill"></i> Home</a
            >
          </li>
          <li class="nav-item">
            <a class="nav-link" href="/news"
              ><i class="bi bi-newspaper"></i> News</a
            >
          </li>
          <li class="nav-item">
            <a class="nav-link" href="/users"
              ><i class="bi bi-people-fill"></i> Users</a
            >
          </li>
          <li class="nav-item">
            <a class="nav-link" href="/games"
              ><i class="bi bi-joystick"></i> Games</a
            >
          </li>
          <li class="nav-item">
            <a class="nav-link" href="/platforms"
              ><i class="bi bi-controller"></i> Platforms</a
            >
          </li>
          <li class="nav-item">
            <a class="nav-link" href="/manual-tracking"
              ><i class="bi bi-clock-history"></i> Manual Tracking</a
            >
          </li>

          <li class="nav-item">
            <a class="nav-link" href="/help"
              ><i class="bi bi-question-circle"></i> Help</a
            >
          </li>

          <li v-if="!sessionUser" class="nav-item">
            <a class="nav-link" href="/authenticate"
              ><i class="bi bi-shield-lock"></i> Authenticate</a
            >
          </li>
        </ul>

        <div
          v-if="sessionUser"
          class="ms-lg-auto mt-3 mt-lg-0 d-flex align-items-center gap-2"
        >
          <small class="navbar-text text-body-secondary">
            Authenticated as
            <a class="text-decoration-none" :href="'/user/' + sessionUser.id">
              {{ sessionUser.display_name }}
            </a>
          </small>
          <button class="btn btn-outline-danger btn-sm" @click="logoutSession">
            Logout
          </button>
        </div>

      </div>
    </div>
  </nav>
</template>
