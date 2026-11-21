import { computed } from "vue";
import { useAuthenticatedUser } from "./useAuthenticatedUser";

const { authenticatedUser } = useAuthenticatedUser();
// opted in on the settings page, everyone else (also when not logged in) gets censored names
const showNsfw = computed(
  () => !!authenticatedUser.value?.permissions.includes("show_nsfw"),
);

type NamedGame = { name: string; nsfw?: boolean };

/** small seeded random number generator (mulberry32), returns 0 <= n < 1 */
function seededRandom(seed: number): () => number {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function hash(text: string): number {
  let h = 0;
  for (const char of text) {
    h = (Math.imul(31, h) + char.charCodeAt(0)) | 0;
  }
  return h;
}

const LETTERS = "abcdefghijklmnopqrstuvwxyz";
const DIGITS = "0123456789";

function pick(characters: string, random: () => number): string {
  return characters[Math.floor(random() * characters.length)];
}

/** shuffling a word like "XXX" does nothing, so it gets random characters instead */
function randomWord(word: string, random: () => number): string {
  let result = word;
  while (result === word) {
    result = [...word]
      .map((char) => {
        if (DIGITS.includes(char)) {
          return pick(DIGITS, random);
        }
        return pick(LETTERS, random);
      })
      .join("");
  }
  return result;
}

function shuffleWord(word: string, random: () => number): string {
  const letters = [...word];
  for (let i = letters.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [letters[i], letters[j]] = [letters[j], letters[i]];
  }
  // the shuffle can land on the original order, rotate it then
  if (letters.join("") === word) {
    letters.push(letters.shift()!);
  }
  return letters.join("");
}

function jumbleWord(word: string, random: () => number): string {
  const lower = word.toLowerCase();
  const allSame = [...lower].every((char) => char === lower[0]);
  let jumbled = shuffleWord(lower, random);
  if (allSame) {
    jumbled = randomWord(lower, random);
  }
  // keep the capitals where they were, so it still looks like a title
  const original = [...word];
  return [...jumbled]
    .map((char, i) => {
      if (original[i] !== original[i].toLowerCase()) {
        return char.toUpperCase();
      }
      return char;
    })
    .join("");
}

/**
 * jumbles the letters of every word, spaces and punctuation are kept: "Some Juicy Title" -> "Mose Ucjyi Etlit".
 * words that are all the same character ("XXX") get random characters instead.
 * the same text always comes out the same way
 */
export function censor(text: string): string {
  const random = seededRandom(hash(text));
  return text.replace(/[\p{L}\p{N}]+/gu, (word) => {
    if ([...word].length < 2) {
      return word;
    }
    return jumbleWord(word, random);
  });
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
