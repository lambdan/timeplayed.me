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
        I am playing a game on a platform that does not support automatic
        tracking through Discord. How can I track it here, manually?
      </h2>
      <p>
        By DMing the bot manually. The best way to do it to use the
        <code>!start</code> and <code>!stop</code> commands:
      </p>
      <ul>
        <li>
          First off, you probably want to set your default platform (otherwise
          it will show up as unknown)
          <ul>
            <li>
              For example, to make your default <i>mobile</i> you would send:
              <code>!set_default_platform mobile</code> (or use the shortcut:
              <code>!sdp mobile</code>)
            </li>
            <li>
              Send <code>!platforms</code> to see the full list of available
              platforms. Only admins can create new platforms, so if yours is
              missing, just ask an admin to add it for you.
            </li>
          </ul>
        </li>
        <li>
          <code>!start game_id</code> - send this when you start playing
          <ul>
            <li>
              If it's a distinct game name, or the game has an alias, you can
              try using that instead, eg <code>!start roblox</code> or
              <code>!start lol</code>
            </li>
            <li>
              If it's a game that does not exist in the database, you will need
              to add it by supplying a SteamGridDB id. You can use
              <code>!ssgdb game name</code> to search SteamGridDB for games, and
              then <code>!add_sgdb 1234</code> to add the game.
              <ul>
                <li>
                  If the game does not exist on SteamGridDB, an admin will need
                  to add it manually.
                </li>
              </ul>
            </li>
          </ul>
        </li>

        <li><code>!stop</code> - send this when you stop playing</li>
      </ul>
      <p>Easy as that.</p>
      <p>
        Alternatively you can add retroactively if you want to wing it:
        <code>!add game_id h:m:s</code>
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
    </div>
  </div>
</template>
