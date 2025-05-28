import { server } from "./server";

export const PROD = process.env.NODE_ENV === "production";

new server().run();
