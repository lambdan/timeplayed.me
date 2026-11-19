import { computed } from "vue";
import { useAuthenticatedUser } from "./useAuthenticatedUser";

const { authenticatedUser } = useAuthenticatedUser();
// opted in on the settings page, everyone else (also when not logged in) gets censored names
const showNsfw = computed(
  () => !!authenticatedUser.value?.permissions.includes("show_nsfw"),
);

type NamedGame = { name: string; nsfw?: boolean };

/** every letter becomes a *, spaces are kept: "Some Juicy Title" -> "**** ***** *****" */
export function censor(text: string): string {
  return text.replace(/\S/g, "*");
}

export function useNsfw() {
  function isCensored(game: { nsfw?: boolean } | undefined): boolean {
    return !!game?.nsfw && !showNsfw.value;
  }

  /** for places that need a plain string (charts, titles), otherwise use GameName */
  function gameName(game: NamedGame): string {
    return isCensored(game) ? censor(game.name) : game.name;
  }

  return { showNsfw, isCensored, gameName };
}
