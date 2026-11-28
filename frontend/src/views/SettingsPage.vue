<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
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
const anonymous = ref(false);
const hidePlaying = ref(false);
const isPrivate = ref(false);
// as "#rrggbb" for the color inputs, "" for none
const colorPrimary = ref("");
const colorSecondary = ref("");
// activity still on "Unknown", offered to move when picking an OS for the first time.
// Only what the user can see, the backend moves their hidden activity too
const pcActivityCount = ref(0);
const movePcActivity = ref(false);
const saving = ref(false);
const saved = ref(false);
const error = ref("");

// the users current settings, also when they log in on this page
watch(
  authenticatedUser,
  (user) => {
    pcPlatform.value = user?.pc_platform as PCPlatform | undefined;
    showNsfw.value = !!user?.permissions.includes("show_nsfw");
    anonymous.value = !!user?.permissions.includes("anonymous");
    hidePlaying.value = !!user?.permissions.includes("hide_playing");
    isPrivate.value = !!user?.permissions.includes("private");
    colorPrimary.value = user?.color_primary ? "#" + user.color_primary : "";
    colorSecondary.value = user?.color_secondary
      ? "#" + user.color_secondary
      : "";
  },
  { immediate: true },
);

// set by an admin, the user can't turn it off
const forcedAnonymous = computed(
  () => !!authenticatedUser.value?.permissions.includes("force_anonymous"),
);

const canMovePcActivity = computed(
  () =>
    authenticatedUser.value?.pc_platform === "pc" &&
    !!authenticatedUser.value?.permissions.includes("manual_activity") &&
    pcPlatform.value !== "pc" &&
    pcActivityCount.value > 0,
);

async function loadPcActivityCount() {
  pcActivityCount.value = 0;
  const user = authenticatedUser.value;
  const pc = platforms.value.find((p) => p.abbreviation === "pc");
  if (!user || user.pc_platform !== "pc" || !pc) return;
  const totals = await TimeplayedAPI.getTotals({
    users: String(user.id),
    platforms: String(pc.id),
  });
  pcActivityCount.value = totals.activity_count;
}
// needs both the user and the platforms (to find "pc"), whichever arrives last
watch([authenticatedUser, platforms], loadPcActivityCount);

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
      anonymous: anonymous.value,
      hide_playing: hidePlaying.value,
      private: isPrivate.value,
      color_primary: colorPrimary.value,
      color_secondary: colorSecondary.value,
      move_pc_activity: canMovePcActivity.value && movePcActivity.value,
    });
    movePcActivity.value = false;
    await refreshAuthenticatedUser();
    saved.value = true;
  } catch (e: any) {
    error.value = e?.detail || "Saving failed";
  } finally {
    saving.value = false;
  }
}

onMounted(async () => {
  const all: Platform[] = [];
  let offset = 0;
  while (true) {
    const incoming = await TimeplayedAPI.getPlatforms({ offset, limit: 100 });
    all.push(...incoming);
    if (incoming.length < 100) break;
    offset += 100;
  }
  all.sort((a, b) => a.display_name.localeCompare(b.display_name));
  // set all at once, so the watch on platforms sees it
  platforms.value = all;
});
</script>

<template>
  <div class="mx-auto" style="max-width: 600px">
    <h1 class="mb-3">Settings</h1>
    <div v-if="loadingAuthenticatedUser" class="text-center">
      <div class="spinner-border spinner-border-sm" role="status"></div>
    </div>
    <p v-else-if="!authenticatedUser" class="mb-0">
      <a href="/login">Log in</a> to change your settings.
    </p>
    <form v-else @submit.prevent="save">
      <div class="mb-3">
        <label for="pc-platform" class="form-label">PC operating system</label>
        <select id="pc-platform" v-model="pcPlatform" class="form-select">
          <option v-for="p in PC_PLATFORMS" :key="p" :value="p">
            {{ p === "pc" ? "Unknown" : pcPlatformName(p) }}
          </option>
        </select>
        <div class="form-text">Count Discord PC activity under this OS.</div>
        <div v-if="canMovePcActivity && pcPlatform" class="form-check mt-2">
          <input
            id="move-pc-activity"
            v-model="movePcActivity"
            class="form-check-input"
            type="checkbox"
          />
          <label for="move-pc-activity" class="form-check-label">
            Also move my {{ pcActivityCount }}
            {{ pcActivityCount === 1 ? "activity" : "activities" }} on Unknown
            to {{ pcPlatformName(pcPlatform) }}
          </label>
        </div>
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
          Show titles and covers of NSFW games. When off, titles are scrambled
          and covers are blurred.
        </div>
      </div>

      <hr />

      <div class="mb-3">
        <label class="form-label">Colors</label>
        <div class="row g-2 align-items-end">
          <div class="col-auto">
            <label for="color-primary" class="form-label small mb-0"
              >Page</label
            >
            <input
              id="color-primary"
              v-model="colorPrimary"
              class="form-control form-control-color"
              type="color"
            />
          </div>
          <div class="col-auto">
            <label for="color-secondary" class="form-label small mb-0"
              >Charts</label
            >
            <input
              id="color-secondary"
              v-model="colorSecondary"
              class="form-control form-control-color"
              type="color"
            />
          </div>
          <div class="col-auto">
            <button
              type="button"
              class="btn btn-outline-secondary"
              @click="
                colorPrimary = '';
                colorSecondary = '';
              "
            >
              Default
            </button>
          </div>
        </div>
        <div class="form-text">
          Your user page in your colors. Chart colors that are hard to read
          aren't used.
        </div>
      </div>

      <hr />

      <div class="mb-3">
        <h3>Privacy</h3>
        <p>
          Note that these settings only apply to the website (and API). How you
          appear in Discord is unaffected.
        </p>
        <label for="anonymous" class="form-label">Anonymous</label>
        <div class="form-check form-switch">
          <input
            id="anonymous"
            :checked="anonymous || forcedAnonymous"
            :disabled="forcedAnonymous"
            class="form-check-input"
            type="checkbox"
            role="switch"
            @change="anonymous = ($event.target as HTMLInputElement).checked"
          />
        </div>
        <div class="form-text">
          Replace your name and avatar with generic ones.
        </div>
        <div v-if="forcedAnonymous" class="form-text">
          Forced on by an admin due to inappropriate name or avatar. Contact an
          admin if you believe this is a mistake.
        </div>
      </div>

      <div class="mb-3">
        <label for="hide-playing" class="form-label"
          >Hide from now playing</label
        >
        <div class="form-check form-switch">
          <input
            id="hide-playing"
            v-model="hidePlaying"
            class="form-check-input"
            type="checkbox"
            role="switch"
          />
        </div>
      </div>

      <div class="mb-3">
        <label for="private" class="form-label">Private</label>
        <div class="form-check form-switch">
          <input
            id="private"
            v-model="isPrivate"
            class="form-check-input"
            type="checkbox"
            role="switch"
          />
        </div>
        <div class="form-text">
          Hides your profile, activity and stats, excluding them from global
          stats. Only you can see what you've played.
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
</template>
