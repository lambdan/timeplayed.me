<template>
  <div class="card p-0">
    <h1 class="card-header">News</h1>

    <div class="card-body text-start">
      <strong>2025-12-16: Version 3.0.0</strong>
      <p>Happy to announce that version 3.0 of timeplayed.me is now live!</p>
      <ul>
        <li>
          Backend has been completely rewritten, more or less, to be able to
          have before/after parameters everywhere.
          <ul>
            <li>
              The old API was something I threw together very quickly, mostly
              during a car ride, and I didn't know how to use typings in FastAPI
              or anything. Now I know a bit more, so it's less of a mess and
              more maintainable.
            </li>
          </ul>
        </li>
        <li>
          The frontend now have typings based directly on the API, thanks to
          <code>openapi-typescript</code>
        </li>
        <li>
          You can now set a time span/range on most (if not all...) tables
        </li>
        <li>
          The tables have been rewritten. I tried to do some custom stuff with
          the one in 2.0 but it was a mess. This is one is just a plain
          Bootstrap table.
        </li>
        <li>Platforms now have individual pages</li>
      </ul>

      <p>
        I still have more work to do, but this is good enough for a new release
        I think... I want to go to sleep...
      </p>
      <i>-djs</i>
      <hr />

      <strong>2025-07-06: Incident</strong>
      <p>
        Due to a series of mishaps,
        <b
          >sessions between approximately 2025-07-06 01:00-14:40 (Swedish time)
          may have been lost</b
        >. I say may have, because I don't know if anyone actually played
        anything during that time. <br /><br />
        This was because I manually added some sessions I had played, but
        accidentally set the wrong game one entry. So I used the
        <code>!setgame</code> command to change it, but it turns out that
        command had a problem where it changed the game for ALL sessions!
        Yikes... <br /><br />
        Fortunately, I am backing up the database daily. Unfortunately, it is
        done on midnight UTC, so the backup containing data for 2025-07-05 had
        not been done yet, so I had to resort to the backup from the night
        before.
        <br /><br />
        I then extracted the messed up database of 2025-07-05 (which had all the
        games set to one single game (<i>Serious Sam: Xbox</i> if you are
        curious)), and <i>manually</i> inserted the sessions of 2025-07-05 into
        the backup from the day before. <br /><br />
        Fortunately, I had the most sessions that day, so I knew what games I
        had played, and I also visit the website frequently so I have a decent
        idea of what people are playing, so I could make some educated guesses
        on the others. If I guessed wrong, feel free to change it using the
        <code>!setgame</code> command, it should work now 🤞
        <br />
        Then I went to bed, thinking everything was fine.
        <br /><br />
        The next day, while working on preventing stuff like this from happening
        again (more on that soon), I noticed my test sessions weren't saving. It
        turns out, because I had manually manipulated some sessions earlier, the
        sequence numbers in the database was messed up, and so the bot would not
        insert any new entries because the id's were conflicting. I actually had
        a similar problem earlier, when I was migrating from v1 of storage to
        v2, and I fixed that then by resetting the sequences after migration.
        But I very recently removed this part of the code, because the migration
        was done so I figured it wasn't needed anymore... Well anyway, the
        sequence resetting is back now, and everything is fine again.
        <br /><br />
        To hopefully prevent something like this happening again, though you
        should not underestimate my stupidity, I've done a few things:
      </p>

      <ul>
        <li>The database is now backed up hourly, instead of daily</li>
        <li>
          I've set up additional logging. This way, if something screws up I can
          atleast manually go through the logs and recreate what is lost, should
          there be need to.
        </li>
      </ul>
      I could keep quiet about this, because most likely no one even noticed
      this happened, but I want to be transparent about incidents like this to
      build trust.
      <br /><i>-djs</i>

      <hr />
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
        But, the website is now decent enough for now. Maybe I will actually
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
