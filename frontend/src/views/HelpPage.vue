<script lang="ts" setup></script>

<template>
  <div class="card" style="max-width: 900px; margin: auto">
    <h1 class="card-header">Help</h1>

    <div class="card-body">
      <ul>
        <li>
          <a href="#automatic-tracking">Automatic tracking</a>
          <ul>
            <li>
              <a href="#what-is-tracked">What is automatically tracked?</a>
            </li>
            <li>
              <a href="#consoles">Can I track games played on consoles?</a>
            </li>
            <li>
              <a href="#game-not-showing"
                >I played a game, but it doesn't show up?</a
              >
            </li>
            <li>
              <a href="#rename-game"
                >My game shows up as <code>game.exe</code>. Can I rename it?</a
              >
            </li>
            <li>
              <a href="#ignore-game"
                >How can I ignore a game I don't want to track?</a
              >
            </li>
          </ul>
        </li>
        <li>
          <a href="#manual-tracking-section">Manual tracking</a>
          <ul>
            <li>
              <a href="#manual-tracking"
                >How can I track a game that doesn't show up on Discord?</a
              >
            </li>
            <li>
              <a href="#add-offline"
                >How can I add a game I played offline afterwards?</a
              >
            </li>
          </ul>
        </li>
        <li>
          <a href="#settings">Settings</a>
          <ul>
            <li>
              <a href="#pc-platform"
                >How can my activities show up as Mac or Linux?</a
              >
            </li>
            <li>
              <a href="#nsfw">Why are some game titles shown as ****?</a>
            </li>
          </ul>
        </li>
        <li>
          <a href="#api-section">API</a>
          <ul>
            <li>
              <a href="#api">Is there any other way to track my playtime?</a>
            </li>
          </ul>
        </li>
      </ul>

      <hr />

      <h2 id="automatic-tracking">Automatic tracking</h2>

      <h5 id="what-is-tracked" class="mt-4">What is automatically tracked?</h5>
      <p>
        Basically, if you can see on your Discord profile that you are playing
        something, it will be tracked:
      </p>
      <div class="row">
        <div class="col-lg-6">
          <img src="/images/playing_profile.png" class="img-fluid mb-2" />
          <p>Or in the user list:</p>
          <img src="/images/playing_list.png" class="img-fluid mb-3" />
        </div>
      </div>
      <p>
        Once you stop playing, the bot will notice and send the duration in.
      </p>

      <h5 id="consoles" class="mt-4">Can I track games played on consoles?</h5>
      <p>
        Yes, on consoles that can show your activity in Discord, such as
        PlayStation and Xbox. For this to work, your PlayStation Network or Xbox
        Live account needs to be connected to Discord, with it displayed as your
        status. You can do that in Discord under User Settings → Connections:
      </p>
      <div class="row">
        <div class="col-lg-6">
          <img src="/images/psn_connection.png" class="img-fluid mb-3" />
        </div>
      </div>

      <h5 id="game-not-showing" class="mt-4">
        I played a game, but it doesn't show up?
      </h5>
      <ul>
        <li>Sessions shorter than 30 seconds are discarded.</li>
        <li>
          Ensure you have activity sharing enabled on Discord. If you have a
          game running, and you can't see it under your name in the server's
          user list, the bot can't see it either (see above).
        </li>
        <li>
          If it works for other games, it is possible your game is doing
          something weird with its activity duration. For example, Mass Effect
          Legendary Edition will start a new session (resetting the playtime)
          when you quit out to the launcher.
        </li>
      </ul>

      <h5 id="rename-game" class="mt-4">
        I added a game manually to Discord, but it's showing up as
        <code>game.exe</code>. Can I rename it so it automatically gets properly
        named here?
      </h5>
      <p>
        If you go into the Registered Games section in Discord settings, you can
        click a <strong>non-verified</strong> game's title to rename it to
        whatever you want.
      </p>
      <p>
        To change the game of an activity that's already saved, open the
        activity and click the <i class="bi bi-pencil"></i> next to its game.
      </p>

      <h5 id="ignore-game" class="mt-4">
        I don't want to track a particular game I am playing. How can I ignore
        it?
      </h5>
      <p>
        Go into the Registered Games section of Discord and click the eye to
        toggle detection. (Note that this hides the game from all of Discord).
      </p>
      <p>
        Alternatively you can delete the session afterwards: open the activity
        and click the <i class="bi bi-trash"></i> next to its title.
      </p>

      <hr />

      <h2 id="manual-tracking-section">Manual tracking</h2>

      <h5 id="manual-tracking" class="mt-4">
        I am playing a game on a platform that does not show up on Discord. How
        can I track it here, manually?
      </h5>
      <p>Use the <a href="/manual-tracking">manual tracking page</a>.</p>

      <h5 id="add-offline" class="mt-4">
        I played a game while I was on an airplane/offline. How can I add it
        retroactively?
      </h5>
      <p>Use the <a href="/manual-tracking">manual tracking page</a>.</p>

      <hr />

      <h2 id="settings">Settings</h2>

      <h5 id="pc-platform" class="mt-4">
        I use a Mac or Linux, and want my activities to show up as such instead
        of Windows.
      </h5>
      <p>
        Set your Discord PC platform on the
        <a href="/settings">settings page</a>.
      </p>
      <p>
        To change the platform of an activity that's already saved, open the
        activity and click the <i class="bi bi-pencil"></i> next to its
        platform.
      </p>

      <h5 id="nsfw" class="mt-4">Why are some game titles shown as ****?</h5>
      <p>
        They're NSFW games. Turn on <i>Show NSFW games</i> on the
        <a href="/settings">settings page</a> to see their titles and covers.
      </p>

      <hr />

      <h2 id="api-section">API</h2>

      <h5 id="api" class="mt-4">
        Apart from Discord and the manual tracking page, is there any other way
        to track my playtime?
      </h5>
      <p>
        Yes, there is an API which you can use to send in playtime. See the
        <a href="/api/docs">API documentation</a>, in particular the
        <a href="/api/docs#/authenticated/add_activity_activity_post"
          >Add Activity endpoint</a
        >.
      </p>
      <p>Here are some example scripts I've made for Linux:</p>
      <ul>
        <li>
          <a
            href="https://gist.github.com/lambdan/440b5dd4a6fb264716234b153fe6073b"
            >tp.bash</a
          >
        </li>
        <li>
          <a
            href="https://gist.github.com/lambdan/4639e3a451b94b6e38ae1e31f99f7838"
            >tp.steam.bash</a
          >
        </li>
      </ul>
      <p>
        To authenticate with the API you need a token, send
        <code>!token</code> to the bot in a DM to get one.
      </p>
    </div>
  </div>
</template>
