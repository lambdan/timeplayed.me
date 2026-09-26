import { ref } from "vue";

const API_TOKEN_KEY = "api-token";
const initialToken = localStorage.getItem(API_TOKEN_KEY);

const token = ref<string | null>(initialToken);

export function useApiToken() {
  function setApiToken(nextToken: string) {
    token.value = nextToken;
    localStorage.setItem(API_TOKEN_KEY, nextToken);
  }

  function clearApiToken() {
    token.value = null;
    localStorage.removeItem(API_TOKEN_KEY);
  }

  return {
    token,
    setApiToken,
    clearApiToken,
  };
}
