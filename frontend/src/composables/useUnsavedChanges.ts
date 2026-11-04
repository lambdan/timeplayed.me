import { onUnmounted } from "vue";

// every mounted editor that can have unsaved changes
const editors = new Map<symbol, { name: string; unsaved: () => string[] }>();

function unsavedLines(): string[] {
  return [...editors.values()]
    .map((e) => ({ name: e.name, unsaved: e.unsaved() }))
    .filter((e) => e.unsaved.length > 0)
    .map((e) => `${e.name}: ${e.unsaved.join(", ")}`);
}

export function hasUnsavedChanges(): boolean {
  return unsavedLines().length > 0;
}

/** true if there's nothing unsaved, or the user is fine with losing it */
export function confirmDiscard(): boolean {
  const lines = unsavedLines();
  if (lines.length === 0) return true;
  const list = lines.map((line) => `- ${line}`).join("\n");
  return window.confirm(`Unsaved changes:\n${list}\n\nDiscard them?`);
}

// leaving the page (links, reload, closing the tab) gets the browsers own prompt
window.addEventListener("beforeunload", (event) => {
  if (hasUnsavedChanges()) event.preventDefault();
});

/**
 * registers an editor for as long as the component is mounted.
 * name is shown in the prompt (eg "game"), unsaved lists what isn't saved
 */
export function useUnsavedChanges(name: string, unsaved: () => string[]) {
  const key = Symbol(name);
  editors.set(key, { name, unsaved });
  onUnmounted(() => editors.delete(key));
}
