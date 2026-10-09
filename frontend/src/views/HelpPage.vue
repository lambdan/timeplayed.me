<script lang="ts" setup></script>

<template>
  <div
    class="card p-0"
    style="max-width: 900px; margin: auto; margin-top: 2rem"
  >
    <h1 class="card-header">Help</h1>

    <div class="card-body">
      <a name="what-is-tracked"></a>
      <h2>What is automatically tracked?</h2>
      <p>
        Basically, if you can see on your Discord profile that you are playing
        something, it will be tracked:
      </p>

      <div
        class="row"
        style="
          display: flex;
          flex-wrap: wrap;
          justify-content: center;
          max-width: 500px;
        "
      >
        <img src="/images/playing_profile.png" class="img-fluid mb-2" />
        <p>Or in the user list:</p>
        <img src="/images/playing_list.png" class="img-fluid mb-4" />
      </div>

      <p>
        Once you stop playing, the bot will notice and send the duration in.
      </p>

      <hr />

      <a name="manual-tracking"></a>
      <h2>
        I am playing a game on a platform that does not show up on Discord. How
        can I track it here, manually?
      </h2>
      <p>
        Use the <a href="/manual-tracking">manual tracking page</a> or DM the
        bot (send <code>!help start</code>).
      </p>
      <hr />

      <a name="game-not-showing"></a>
      <h2>I played a game, but it doesn't show up?</h2>
      <ul>
        <li>Sessions shorter than 30 seconds are discarded.</li>
        <li>
          Ensure you have activity sharing enabled on Discord. If you have a
          game running, and you can't see it under your name in the server's
          user list, the bot can't see it either (see above).
        </li>
        <li>
          If it works for other games, it is possible your game is doing
          something weird with it's activity duration. For example, Mass Effect
          Legendary Edition will start a new session (resetting the playtime)
          when you quit out to the launcher.
        </li>
      </ul>

      <hr />

      <a name="rename-game"></a>
      <h2>
        I added a game manually to Discord, but it's showing up as
        <code>game.exe</code>. Can I rename it so it automatically gets properly
        named here?
      </h2>
      <ul>
        <li>
          If you go into the Registered Games section in Discord settings, you
          can click a <strong>non-verified</strong> game's title to rename it to
          whatever you want.
        </li>
        <li>
          You can also use the <code>!set_game</code> command to change an
          activity's game retroactively
        </li>
      </ul>

      <hr />

      <a name="ignore-game"></a>
      <h2>
        I don't want to track a particular game I am playing. How can I ignore
        it?
      </h2>
      <p>
        Go into the Registered Games section of Discord and click the eye to
        toggle detection. (Note that this hides the game from all of Discord).
      </p>
      <p>
        Alternatively you can remove the session afterwards using the
        <code>!remove</code> command
      </p>

      <hr />

      <a name="add-offline"></a>
      <h2>
        I played a game while I was on an airplane/offline. How can I add it
        retroactively?
      </h2>
      <p>
        By using the <code>!add</code> command:
        <code>!add game_id h:m:s</code>
      </p>

      <hr />

      <a name="pc-platform"></a>
      <h2>
        I use a Mac or Linux, and want my activities to show up as such instead
        of Windows.
      </h2>
      <p>
        Use the <code>!pcplatform</code> (or shortcut: <code>!pcp</code>)
        command to change what your PC platform is, eg <code>!pcp mac</code>
      </p>
      <p>You can also retroactively update using <code>!set_platform</code>.</p>

      <hr />

      <a name="api"></a>
      <h2>
        Apart from Discord and the manual tracking page, is there any other way
        to track my playtime?
      </h2>
      <p>
        Yes, there is an API which you can use to send in playtime. See the
        <a href="/api/docs">API documentation</a>, in particular the
        <a href="/api/docs#/authenticated/add_activity_api_activity_post"
          >Add Activity endpoint</a
        >. <br />For example, if you're on Linux, you can make a
        <a
          href="https://gist.github.com/lambdan/440b5dd4a6fb264716234b153fe6073b"
          >simple shell script</a
        >
        that sends playtime data to the API using curl that can easily be used
        together with Steam.
      </p>
      <p>
        To authenticate with the API you need a token, send
        <code>!token</code> to the bot in a DM to get one.
      </p>
    </div>
  </div>
</template>
