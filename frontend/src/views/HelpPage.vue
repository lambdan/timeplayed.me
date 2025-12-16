<script lang="ts" setup></script>

<template>
  <div class="card p-0">
    <h1 class="card-header">Help</h1>

    <div class="card-body text-start">
      <a name="#faq"></a>

      <strong>I played a game, but it doesn't show up?</strong>
      <ul>
        <li>
          Ensure you have activity sharing enabled on Discord. If you have a
          game running, and you can't see it under your name in the server's
          user list, the bot can't see it either.
        </li>
        <li>Sessions shorter than 1 minute are not saved</li>
        <li>
          If it works for other games, it is possible your game is doing
          something weird with it's activity duration. For example, Mass Effect
          Legendary Edition will start a new session (resetting the playtime)
          when you quit out to the launcher.
        </li>
      </ul>

      <strong
        >I added a game manually to Discord, but it's showing up as
        <code>blabla</code>. Can I rename it so it automatically gets properly
        named here?</strong
      >
      <ul>
        <li>
          If you go into the Registered Games section in Discord settings, you
          can click a <strong>non-verified</strong> game's title to rename it to
          whatever you want.
        </li>
        <li>
          You can also use the <code>!setgame</code> command to change an
          activity's game retroactively
        </li>
      </ul>
      <strong
        >I don't want to track a particular game I am playing. How can I ignore
        it?</strong
      >
      <ul>
        <li>
          Go into the Registered Games section of Discord and click the eye to
          toggle detection. (Note that this hides the game from all of Discord).
        </li>
        <li>
          You Alternatively you can remove the session afterwards using the
          <code>!remove</code> command
        </li>
      </ul>

      <strong
        >I am playing a game on a console/platform that doesn't have Discord.
        How can I track it here, manually?</strong
      >
      <p>
        By DMing the timeplayed bot manually. The best way to do it to use the
        <code>!start</code> and <code>!stop</code> commands:
      </p>
      <ul>
        <li>
          <code>!start "Game Name"</code> - send this when you start playing
        </li>
        <li><code>!stop</code> - send this when you stop playing</li>
      </ul>
      <p>Easy as that.</p>

      <strong>
        I played a game while I was on an airplane/offline. How can I add it
        retroactively?
      </strong>
      <p>By using the <code>!add</code> command:</p>
      <ul>
        <li>
          <code>!add "Game Name" 30m</code> - register that you played Game Name
          for 30 minutes
        </li>
      </ul>
    </div>
  </div>
</template>
