import { createApp } from "vue";
import "./style.css";
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap-icons/font/bootstrap-icons.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js"; // Add Bootstrap JS
import App from "./App.vue";
import { router } from "./router";

const app = createApp(App);
app.use(router);
app.mount("#app");
