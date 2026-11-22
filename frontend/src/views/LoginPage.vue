<script setup lang="ts">
import { ref } from "vue";
import { useAuthenticatedUser } from "../composables/useAuthenticatedUser";

const { authenticatedUser, authenticateWithToken, logoutSession } =
  useAuthenticatedUser();
const pendingToken = ref("");
const authError = ref("");
const authenticating = ref(false);

async function authenticateSession() {
  authError.value = "";
  const nextToken = pendingToken.value.trim();
  if (!nextToken) {
    authError.value = "Please enter your token.";
    return;
  }

  authenticating.value = true;
  try {
    await authenticateWithToken(nextToken);
    pendingToken.value = "";
  } catch (err: any) {
    authError.value = err?.message || "Authorization failed.";
  } finally {
    authenticating.value = false;
  }
}

function logoutCurrentSession() {
  logoutSession();
  authError.value = "";
}
</script>

<template>
  <div class="mx-auto" style="max-width: 840px">
    <h1 class="mb-3">Log in</h1>
    <div class="alert alert-secondary">
      Logging in with a token from the Discord bot is
      <strong>completely optional</strong>, but it lets you track playtime
      manually, edit or delete your activities, and change your settings.
    </div>

    <div v-if="authenticatedUser" class="alert alert-success mb-3">
      Signed in as
      <a class="text-decoration-none" :href="'/user/' + authenticatedUser.id">
        {{ authenticatedUser.display_name }}
      </a>
    </div>

    <div v-if="!authenticatedUser">
      <div class="input-group">
        <input
          v-model="pendingToken"
          type="password"
          class="form-control"
          placeholder="Enter API token"
          @keydown.enter.prevent="authenticateSession"
        />
        <button
          class="btn btn-primary"
          @click="authenticateSession"
          :disabled="authenticating"
        >
          {{ authenticating ? "Logging in..." : "Log in" }}
        </button>
      </div>

      <p class="text-secondary mt-3 mb-0">
        Get a token by sending <code>!token</code> to the bot in Discord.
      </p>
      <div v-if="authError" class="alert alert-danger mt-3 mb-0">
        {{ authError }}
      </div>
    </div>

    <div class="d-flex gap-2 mt-3">
      <button
        v-if="authenticatedUser"
        class="btn btn-outline-danger"
        @click="logoutCurrentSession"
      >
        Logout
      </button>
    </div>
    <p class="text-body-secondary small mt-3 mb-0" v-if="authenticatedUser">
      Clicking logout here only removes your API token from this browser. The
      token (and any other active tokens) still remains valid on the server. To
      invalidate all of your tokens, DM the bot
      <code>!revoke_tokens</code>.
    </p>
  </div>
</template>
