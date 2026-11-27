<script setup lang="ts">
import { useAuthenticatedUser } from "../composables/useAuthenticatedUser";
import DiscordAvatar from "./DiscordAvatar.vue";

const { authenticatedUser, isAdmin, logoutSession } = useAuthenticatedUser();
</script>

<template>
  <nav class="navbar navbar-expand-lg bg-body-tertiary">
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
        <ul class="navbar-nav gap-1">
          <li class="nav-item">
            <a class="nav-link" href="/">
              <i class="bi bi-house-fill"></i> Home</a
            >
          </li>
          <!-- users, games and platforms are reached through browse -->
          <li class="nav-item">
            <a class="nav-link" href="/browse"
              ><i class="bi bi-search"></i> Browse</a
            >
          </li>
          <li class="nav-item">
            <a class="nav-link" href="/stats"
              ><i class="bi bi-bar-chart-fill"></i> Stats</a
            >
          </li>
          <li class="nav-item">
            <a class="nav-link" href="/manual-tracking"
              ><i class="bi bi-stopwatch"></i> Manual Tracking</a
            >
          </li>

          <li class="nav-item">
            <a class="nav-link" href="/help"
              ><i class="bi bi-question-circle"></i> Help</a
            >
          </li>

          <li v-if="isAdmin" class="nav-item">
            <a class="btn btn-outline-warning" href="/admin"
              ><i class="bi bi-shield-fill-exclamation"></i> Admin</a
            >
          </li>

          <li v-if="!authenticatedUser" class="nav-item">
            <a class="nav-link" href="/login"
              ><i class="bi bi-shield-lock"></i> Log in</a
            >
          </li>
        </ul>

        <!-- a navbar-nav dropdown: on phones the menu opens inline in the collapsed navbar -->
        <ul v-if="authenticatedUser" class="navbar-nav ms-lg-auto">
          <li class="nav-item dropdown">
            <button
              class="nav-link d-flex align-items-center gap-2 rounded-pill py-lg-0"
              type="button"
              data-bs-toggle="dropdown"
              aria-expanded="false"
              :aria-label="authenticatedUser.display_name"
            >
              <DiscordAvatar
                :user="authenticatedUser"
                :link="false"
                :maxWidth="36"
                :classes="['rounded-circle']"
              />
              <!-- in the collapsed menu on phones the avatar alone would look lost -->
              <span class="d-lg-none">{{
                authenticatedUser.display_name
              }}</span>
            </button>
            <ul class="dropdown-menu dropdown-menu-lg-end">
              <li>
                <a
                  class="dropdown-item"
                  :href="'/user/' + authenticatedUser.id"
                >
                  <i class="bi bi-person"></i>
                  {{ authenticatedUser.display_name }}
                </a>
              </li>
              <li>
                <a class="dropdown-item" href="/settings">
                  <i class="bi bi-gear"></i> Settings
                </a>
              </li>
              <li><hr class="dropdown-divider" /></li>
              <li>
                <button
                  class="dropdown-item text-danger"
                  @click="logoutSession"
                >
                  <i class="bi bi-box-arrow-right"></i> Logout
                </button>
              </li>
            </ul>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>
