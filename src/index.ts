import { server } from "./server";

export const APP_VERSION = require("../package.json").version;
export const PROD = process.env.NODE_ENV === "production";
export const APP_STARTED = new Date();

new server().run();
