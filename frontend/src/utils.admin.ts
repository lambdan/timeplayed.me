/** labels for the fields in a patch, for showing what hasn't been saved yet */
export function unsavedFieldLabels<T extends object>(
  patch: T,
  labels: Record<keyof T, string>,
): string[] {
  return (Object.keys(patch) as (keyof T)[]).map((field) => labels[field]);
}
