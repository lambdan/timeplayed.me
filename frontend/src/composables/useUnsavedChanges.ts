import { onUnmounted } from "vue";

// every mounted editor that can have unsaved changes
const checks = new Set<() => boolean>();

export function hasUnsavedChanges(): boolean {
  return [...checks].some((isDirty) => isDirty());
}

/** true if there's nothing unsaved, or the user is fine with losing it */
export function confirmDiscard(): boolean {
  if (!hasUnsavedChanges()) return true;
  return window.confirm("You have unsaved changes. Discard them?");
}

// leaving the page (links, reload, closing the tab) gets the browsers own prompt
window.addEventListener("beforeunload", (event) => {
  if (hasUnsavedChanges()) event.preventDefault();
});

/** registers an editor's unsaved check for as long as the component is mounted */
export function useUnsavedChanges(isDirty: () => boolean) {
  checks.add(isDirty);
  onUnmounted(() => checks.delete(isDirty));
}
