<script lang="ts" setup></script>

<template>
  <div class="card p-0">
    <h1 class="card-header">News</h1>

    <div class="card-body text-start">
      <a name="#faq"></a>
      <h1>FAQ</h1>

      <strong>I played a game for a little while, but it doesn't show up?</strong>
      <ul>
        <li>Sessions shorter than 1 minute are not saved</li>
        <li>
          If it works for other games, it is possible your game is doing
          something weird with it's activity duration. For example, Mass Effect
          Legendary Edition will start a new session (resetting the playtime)
          when you quit out out the launcher.
        </li>
      </ul>

      <strong>I added a game manually to Discord, but it's showing up as
        <code>bla.exe</code>. Can I rename it so it automatically gets properly
        named here?</strong>
      <p>
        Yes, if you go into the Registered Games section in Discord, you can
        click a <strong>non-verified</strong> game's title to rename it to
        whatever you want.
      </p>

      <strong>I don't want to track a particular game I am playing. How can I ignore
        it?</strong>
      <p>
        Go into the Registered Games section of Discord and click the eye to
        toggle detection. (Note that this hides the game from all of Discord).
      </p>
      <p>
        Alternatively you can remove the session afterwards using the
        <code>!remove</code> command
      </p>

      <hr />

      <!--<a name="commands"></a>
      <h1>Commands Reference</h1>-->
    </div>
  </div>
</template>
