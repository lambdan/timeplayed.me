import { computed, effectScope, ref, watch } from "vue";
import type { AuthenticatedUser } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import { useApiToken } from "./useApiToken";

const { token, setApiToken, clearApiToken } = useApiToken();
const authenticatedUser = ref<AuthenticatedUser>();
// only for showing admin stuff, the backend checks the permission on every admin request
const isAdmin = computed(
  () => !!authenticatedUser.value?.permissions.includes("admin"),
);
const loadingAuthenticatedUser = ref(false);
let initialized = false;

async function refreshAuthenticatedUser() {
  if (!token.value) {
    authenticatedUser.value = undefined;
    return;
  }

  try {
    loadingAuthenticatedUser.value = true;
    authenticatedUser.value = await TimeplayedAPI.whoAmI(token.value);
  } catch {
    authenticatedUser.value = undefined;
  } finally {
    loadingAuthenticatedUser.value = false;
  }
}

function ensureInitialized() {
  if (initialized) {
    return;
  }

  initialized = true;
  const scope = effectScope(true);
  scope.run(() => {
    watch(
      token,
      () => {
        refreshAuthenticatedUser();
      },
      { immediate: true },
    );
  });
}

export function useAuthenticatedUser() {
  ensureInitialized();

  async function authenticateWithToken(nextToken: string) {
    const whoAmI = await TimeplayedAPI.whoAmI(nextToken);
    setApiToken(nextToken);
    authenticatedUser.value = whoAmI;
    return whoAmI;
  }

  function logoutSession() {
    clearApiToken();
    authenticatedUser.value = undefined;
  }

  return {
    authenticatedUser,
    isAdmin,
    loadingAuthenticatedUser,
    refreshAuthenticatedUser,
    authenticateWithToken,
    logoutSession,
  };
}
