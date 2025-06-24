<template>
  <div class="card p-0">
    <h1 class="card-header">News</h1>

    <div class="card-body text-start">
      <strong>2025-06-24: Version 2.0.0</strong>
      <p>
        The website has been completely redesigned! It now uses
        <a href="https://vuejs.org/">Vue.js</a> and should be much more
        responsive and just nicer to use in general. <br />For example, loading
        the Games page shouldn't take forever anymore, as the cover art is now
        loaded asynchronously.
        <br />
        There is still work to do, particularly with the backend/the bot,
        oblivionis. I have forked it and added an API to it (which is how the
        website gets its data now) which I want to clean up and provide
        documentation for.<br />
        The commands system has also been pretty neglected while I was
        re-working the frontend, so it has a lot of bugs.
        <br />
        But, the webisite is now decent enough for now. Maybe I will actually
        play some games now!
        <br /><i>-djs</i>
      </p>

      <hr />

      <strong>2025-06-10: Incorrect timestamps</strong>
      <p>
        Due to a bug, sessions played between 2025-06-09 21:48 to 2025-06-10
        17:00 (UTC) have incorrectly gotten their timestamps set to
        <code>Mon, 09 Jun 2025 21:48:24 GMT</code>.
        <br />
        Sorry about that.
        <br />
        A command has been added to the bot that lets you modify the date of a
        session, so you can fix it retroactively: <code>!setdate</code> <br /><i
          >-djs</i
        >
      </p>

      <hr />

      <strong>2025-06-09: Platform support</strong>
      <p>
        Platform is now tracked. Website will better designed soon to show it
        better. It's all very WIP right now. You can also do some commands with
        the bot. Write <code>!help</code> to the bot to see what's possible!
        <br /><i>-djs</i>
      </p>
    </div>
  </div>
</template>
