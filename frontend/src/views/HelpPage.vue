<script lang="ts" setup></script>

<template>
  <div class="card p-0">
    <h1 class="card-header">Help</h1>

    <div class="card-body text-start">
      <a name="#faq"></a>

      <h2>What is automatically tracked?</h2>
      <p>
        Basically, if you can see on your Discord profile that you are playing
        something, it will be tracked:
      </p>

      <img
        src="/images/playing_profile.png"
        class="img-fluid p-4"
        style="max-width: 400px"
      />
      <img
        src="/images/playing_list.png"
        class="img-fluid p-4"
        style="max-width: 400px"
      />

      <p>
        Once you stop playing, the bot will notice and send the duration in.
      </p>

      <hr />

      <h2>I played a game, but it doesn't show up?</h2>
      <p>Sessions shorter than 30 seconds are discarded.</p>
      <p>
        Ensure you have activity sharing enabled on Discord. If you have a game
        running, and you can't see it under your name in the server's user list,
        the bot can't see it either (see above).
      </p>
      <p>
        If it works for other games, it is possible your game is doing something
        weird with it's activity duration. For example, Mass Effect Legendary
        Edition will start a new session (resetting the playtime) when you quit
        out to the launcher.
      </p>

      <hr />

      <h2>
        I added a game manually to Discord, but it's showing up as
        <code>game.exe</code>. Can I rename it so it automatically gets properly
        named here?
      </h2>
      <p>
        If you go into the Registered Games section in Discord settings, you can
        click a <strong>non-verified</strong> game's title to rename it to
        whatever you want.
      </p>
      <p>
        You can also use the <code>!set_game</code> command to change an
        activity's game retroactively
      </p>

      <hr />

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

      <h2>
        I am playing a game on a console/platform that doesn't have Discord. How
        can I track it here, manually?
      </h2>
      <p>
        By DMing the timeplayed bot manually. The best way to do it to use the
        <code>!start</code> and <code>!stop</code> commands:
      </p>
      <ul>
        <li><code>!start game_id</code> - send this when you start playing</li>
        <li><code>!stop</code> - send this when you stop playing</li>
      </ul>
      <p>Easy as that.</p>
      <p>
        If it's a new game to the database, you have to add it first using its
        SteamGridDB ID. You can search for games using `!ssgdb`.
      </p>
      <p>
        If it's a game that does not exist on SteamGridDB, an admin will need to
        add it manually.
      </p>

      <hr />

      <h2>
        I played a game while I was on an airplane/offline. How can I add it
        retroactively?
      </h2>
      <p>By using the <code>!add_activity</code> command:</p>
      <code>!add_activity game_id h:m:s</code>

      <hr />

      <h2>
        I use a Mac or Linux, and want my activities to show up as such instead
        of Windows.
      </h2>
      <p>
        Use the <code>!pcplatform</code> command to change what your PC platform
        is. You can also retroactively update using <code>!set_platform</code>.
      </p>
    </div>
  </div>
</template>
