export interface MergeGame {
    /**
     * The parent game title that will remain in the database
     */
    parent: string;

    /**
     * An array of child game titles that will be merged into the parent title
     */
    children: string[];
}