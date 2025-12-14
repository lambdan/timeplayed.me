<template>
  <nav class="navbar navbar-expand-lg">
    <div class="container">
      <a href="/" class="navbar-brand">timeplayed.me</a>
      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarSupportedContent"
        aria-controls="navbarSupportedContent"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="navbarSupportedContent">
        <ul class="navbar-nav gap-2">
          <li class="nav-item">
            <a class="nav-link" href="/">
              <i class="bi bi-house-fill"></i> Home</a
            >
          </li>
          <li class="nav-item">
            <a class="nav-link" href="/news"
              ><i class="bi bi-newspaper"></i> News</a
            >
          </li>
          <li class="nav-item">
            <a class="nav-link" href="/users"
              ><i class="bi bi-people-fill"></i> Users</a
            >
          </li>
          <li class="nav-item">
            <a class="nav-link" href="/games"
              ><i class="bi bi-joystick"></i> Games</a
            >
          </li>
          <li class="nav-item">
            <a class="nav-link" href="/platforms"
              ><i class="bi bi-controller"></i> Platforms</a
            >
          </li>
          <li class="nav-item">
            <a class="nav-link" href="/help"
              ><i class="bi bi-question-circle"></i> Help</a
            >
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>
