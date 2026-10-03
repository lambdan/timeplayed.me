import { createRouter, createWebHistory } from "vue-router";
import type { RouteRecordRaw } from "vue-router";
import HomePage from "../views/HomePage.vue";
import UserPage from "../views/UserPage.vue";
import NewsPage from "../views/NewsPage.vue";
import UserListPage from "../views/UserListPage.vue";
import GameListPage from "../views/GameListPage.vue";
import PlatformListPage from "../views/PlatformListPage.vue";
import GamePage from "../views/GamePage.vue";
import PlatformPage from "../views/PlatformPage.vue";
import YearRecapUser from "../views/YearRecapUser.vue";
import HelpPage from "../views/HelpPage.vue";
import ActivityPage from "../views/ActivityPage.vue";
import GamePageByIGDB from "../views/GamePageByIGDB.vue";
import ManualTracking from "../views/ManualTracking.vue";
import AuthenticatePage from "../views/AuthenticatePage.vue";
import { updateDocumentTitle } from "../utils.ts";

const routes: RouteRecordRaw[] = [
  // Static pages

  { path: "/", component: HomePage, meta: { title: "Home" } },
  { path: "/news", component: NewsPage, meta: { title: "News" } },
  { path: "/help", component: HelpPage, meta: { title: "Help" } },
  {
    path: "/authenticate",
    component: AuthenticatePage,
    meta: { title: "Authenticate" },
  },
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


router.afterEach((to) => {
  // Update <title> if page itself hasn't already
  if (typeof to.meta?.title === "string") {
    // Default title in index.html
    if (document.title === "Timeplayed.me - Playtime Tracker") {
      updateDocumentTitle(to.meta.title);
      //document.title = `${to.meta.title} - Timeplayed.me`;
    }
  }
});
