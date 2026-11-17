import { useRoute } from "vue-router";
import { updateDocumentTitle } from "../utils";

/**
 * Returns a function that sets the <title>, unless we have navigated away since
 * the page was opened (e.g. its data loaded after clicking a link to another page)
 */
export function usePageTitle() {
  const route = useRoute();
  const path = route.path;
  return (title: string) => {
    if (route.path === path) {
      updateDocumentTitle(title);
    }
  };
}
