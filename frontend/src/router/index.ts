import { createRouter, createWebHistory, START_LOCATION } from "vue-router";
import type { RouteRecordRaw } from "vue-router";
import HomePage from "../views/HomePage.vue";
import UserPage from "../views/UserPage.vue";
import UserListPage from "../views/UserListPage.vue";
import GameListPage from "../views/GameListPage.vue";
import PlatformListPage from "../views/PlatformListPage.vue";
import GamePage from "../views/GamePage.vue";
import PlatformPage from "../views/PlatformPage.vue";
import YearRecapUser from "../views/YearRecapUser.vue";
import HelpPage from "../views/HelpPage.vue";
import StatsPage from "../views/StatsPage.vue";
import BrowsePage from "../views/BrowsePage.vue";
import ActivityPage from "../views/ActivityPage.vue";
import GamePageByIGDB from "../views/GamePageByIGDB.vue";
import ManualTracking from "../views/ManualTracking.vue";
import LoginPage from "../views/LoginPage.vue";
import AdminPage from "../views/AdminPage.vue";
import SettingsPage from "../views/SettingsPage.vue";
import { updateDocumentTitle } from "../utils.ts";

const routes: RouteRecordRaw[] = [
  // Static pages

  { path: "/", component: HomePage, meta: { title: "Home" } },
  // the news page was removed, old links go home
  { path: "/news", redirect: "/" },
  { path: "/stats", component: StatsPage, meta: { title: "Stats" } },
  { path: "/browse", component: BrowsePage, meta: { title: "Browse" } },
  { path: "/help", component: HelpPage, meta: { title: "Help" } },
  {
    path: "/login",
    component: LoginPage,
    meta: { title: "Log in" },
  },
  // the old name, still in bot messages and bookmarks
  { path: "/authenticate", redirect: "/login" },
  { path: "/users", component: UserListPage, meta: { title: "Users" } },
  { path: "/games", component: GameListPage, meta: { title: "Games" } },
  {
    path: "/platforms",
    component: PlatformListPage,
    meta: { title: "Platforms" },
  },
  {
    path: "/manual-tracking",
    name: "ManualTracingPage",
    component: ManualTracking,
    meta: { title: "Manual Tracking" },
  },
  { path: "/admin", component: AdminPage, meta: { title: "Admin" } },
  { path: "/settings", component: SettingsPage, meta: { title: "Settings" } },

  // Dynamic pages

  {
    path: "/activity/:id",
    name: "ActivityPage",
    component: ActivityPage,
    meta: { title: "Activity" },
  },
  {
    path: "/user/:id",
    name: "UserPage",
    component: UserPage,
    meta: { title: "User" },
  },
  {
    path: "/game/:id",
    name: "GamePage",
    component: GamePage,
    meta: { title: "Game" },
  },
  {
    path: "/game_igdb/:id",
    name: "GamePageByIGDB",
    component: GamePageByIGDB,
    meta: { title: "Game (IGDB)" },
  },
  {
    path: "/platform/:id",
    name: "PlatformPage",
    component: PlatformPage,
    meta: { title: "Platform" },
  },
  {
    path: "/user/:id/recap/:year",
    name: "UserRecap",
    component: YearRecapUser,
    meta: { title: "User Recap" },
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.afterEach((to, from) => {
  // The server sends page specific <head> tags for the first page (see index.html).
  // After navigating to another page they would describe the wrong page, so remove them
  if (from !== START_LOCATION && from.path !== to.path) {
    document
      .querySelectorAll(
        'meta[name="description"], link[rel="canonical"], meta[property^="og:"]',
      )
      .forEach((el) => el.remove());
  }

  // Pages with a more specific title (e.g. game name) set it after loading
  if (typeof to.meta?.title === "string") {
    updateDocumentTitle(to.meta.title);
  }
});
