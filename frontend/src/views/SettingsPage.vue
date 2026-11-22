<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { PC_PLATFORMS, type PCPlatform, type Platform } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import { useApiToken } from "../composables/useApiToken";
import { useAuthenticatedUser } from "../composables/useAuthenticatedUser";

const { token } = useApiToken();
const {
  authenticatedUser,
  loadingAuthenticatedUser,
  refreshAuthenticatedUser,
} = useAuthenticatedUser();

const platforms = ref<Platform[]>([]);
const pcPlatform = ref<PCPlatform>();
const showNsfw = ref(false);
const saving = ref(false);
const saved = ref(false);
const error = ref("");

// the users current settings, also when they log in on this page
watch(
  authenticatedUser,
  (user) => {
    pcPlatform.value = user?.pc_platform as PCPlatform | undefined;
    showNsfw.value = !!user?.permissions.includes("show_nsfw");
  },
  { immediate: true },
);

function pcPlatformName(abbreviation: string) {
  const platform = platforms.value.find((p) => p.abbreviation === abbreviation);
  return platform?.display_name ?? abbreviation;
}

async function save() {
  if (!token.value) return;
  saving.value = true;
  saved.value = false;
  error.value = "";
  try {
    await TimeplayedAPI.updateSettings(token.value, {
      pc_platform: pcPlatform.value,
      show_nsfw: showNsfw.value,
    });
    await refreshAuthenticatedUser();
    saved.value = true;
  } catch (e: any) {
    error.value = e?.detail || "Saving failed";
  } finally {
    saving.value = false;
  }
}

onMounted(async () => {
  let offset = 0;
  while (true) {
    const incoming = await TimeplayedAPI.getPlatforms({ offset, limit: 100 });
    platforms.value.push(...incoming);
    if (incoming.length < 100) break;
    offset += 100;
  }
  platforms.value.sort((a, b) => a.display_name.localeCompare(b.display_name));
});
</script>

<template>
  <div class="card mx-auto" style="max-width: 600px">
    <h1 class="card-header">Settings</h1>
    <div class="card-body">
      <div v-if="loadingAuthenticatedUser" class="text-center">
        <div class="spinner-border spinner-border-sm" role="status"></div>
      </div>
      <p v-else-if="!authenticatedUser" class="mb-0">
        <a href="/login">Log in</a> to change your settings.
      </p>
      <form v-else @submit.prevent="save">
        <div class="mb-3">
          <label for="pc-platform" class="form-label"
            >PC operating system</label
          >
          <select id="pc-platform" v-model="pcPlatform" class="form-select">
            <option v-for="p in PC_PLATFORMS" :key="p" :value="p">
              {{ p === "pc" ? "Unknown" : pcPlatformName(p) }}
            </option>
          </select>
          <div class="form-text">Count Discord PC activity under this OS.</div>
        </div>

        <hr />

        <div class="mb-3">
          <label for="show-nsfw" class="form-label">NSFW games</label>
          <div class="form-check form-switch">
            <input
              id="show-nsfw"
              v-model="showNsfw"
              class="form-check-input"
              type="checkbox"
              role="switch"
            />
          </div>
          <div class="form-text">
            Show titles and covers of NSFW games. When off, titles are hidden
            and covers are blurred.
          </div>
        </div>

        <div class="d-flex align-items-center gap-3">
          <button type="submit" class="btn btn-primary" :disabled="saving">
            Save
          </button>
          <span v-if="saved" class="text-success">Saved</span>
          <span v-if="error" class="text-danger">{{ error }}</span>
        </div>
      </form>
    </div>
  </div>
</template>
