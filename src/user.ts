import { Game } from "./game";
import { Session } from "./session";

export class User {
  readonly userID: string;
  readonly sessions: Session[];
  readonly games: Game[];

  constructor(userID: string, sessions: Session[], games: Game[]) {
    this.userID = userID;
    this.sessions = sessions;
    this.games = games;
  }

  /** Returns total playtime for user in seconds */
  totalPlaytime(): number {
    let sum = 0;
    for (const s of this.sessions) {
      sum += s.seconds;
    }
    return sum;
  }

  /** Returns the date of users first session (effectively a registration date) */
  firstSessionDate(): Date {
    return this.sessions[this.sessions.length - 1].date;
    /*
    let oldest = this.sessions[0].date.getTime();
    for (const s of this.sessions) {
      oldest = Math.min(oldest, s.date.getTime());
    }
    return new Date(oldest);*/
  }

  /** Returns when users last session was, effectively when they were last active */
  lastActive(): Date {
    return this.sessions[0].date;
    /*let latest = 0;
    for (const s of this.sessions) {
      latest = Math.max(latest, s.date.getTime());
    }
    return new Date(latest);*/
  }

  /** Returns how many days the user has been active */
  activeDays(): number {
    const days = new Set<string>();
    for (const s of this.sessions) {
      days.add(s.date.toISOString().split("T")[0]);
    }
    return days.size;
  }

  /** Longest gap between sessions, in milliseconds */
  longestGap(): number {
    let longest = 0;
    const sessions = [...this.sessions].reverse();
    for (let i = 1; i < sessions.length; i++) {
      const previous = sessions[i - 1].date;
      const now = sessions[i].date;
      const delta = now.getTime() - previous.getTime();
      //console.warn(previous, now, delta);
      longest = Math.max(longest, delta);
    }
    //console.warn("LONGEST:", longest);
    return longest;
  }

  /** Longest break, in seconds */
  longestBreak(): number {
    const deltaFromNow = Date.now() - this.lastActive().getTime();
    const longest = Math.max(this.longestGap(), deltaFromNow);
    return Math.floor(longest / 1000);
  }

  /** How many days the user played games in a row */
  mostConsecutiveDays(): number {
    const daysPlayed = new Set<string>();
    const sessions = [...this.sessions].reverse();
    for (const s of sessions) {
      const day = s.date.toISOString().split("T")[0];
      daysPlayed.add(day);
    }

    let longestStreak = 0;
    const thisStreak = new Set<string>();
    for (const s of sessions) {
      const thisDay = s.date.toISOString().split("T")[0];
      thisStreak.add(thisDay);
      const nextDay = new Date(s.date.getTime() + 86400 * 1000)
        .toISOString()
        .split("T")[0];

      if (!daysPlayed.has(nextDay)) {
        longestStreak = Math.max(longestStreak, thisStreak.size);
        thisStreak.clear();
      }
    }
    return longestStreak;
  }

  /** Average session length in seconds */
  averageSessionLength(): number {
    return this.totalPlaytime() / this.sessions.length;
  }

  /** Average sessions per game  */
  averageSessionsPerGame(): number {
    return this.sessions.length / this.games.length;
  }

  /** Average playtime per game */
  averagePlaytimePerGame(): number {
    return this.totalPlaytime() / this.games.length;
  }

  chartData() {
    const sessions = [...this.sessions].reverse();
    const playtimeByDateAndGame: Record<string, Record<number, number>> = {};

    // 1. Calculate the first and last dates
    const first = sessions[0].date;
    const today = new Date();

    // 2. Generate an array of all dates from first to last
    let now = new Date(first.getTime());
    const allDatesInRange: string[] = [];

    while (now <= today) {
      allDatesInRange.push(now.toISOString().split("T")[0]); // YYYY-MM-DD
      now = new Date(now.getTime() + 86400 * 1000); // Add 1 day (86400 seconds)
    }
    // Add today if its not in there
    const todayString = today.toISOString().split("T")[0];
    if (!allDatesInRange.includes(todayString)) {
      allDatesInRange.push(todayString);
    }

    // 3. Initialize playtime data for all dates and games
    allDatesInRange.forEach((day) => {
      playtimeByDateAndGame[day] = {};
    });

    // 4. Populate playtime data from the sessions
    sessions.forEach(({ date, gameID, seconds }) => {
      const day = date.toISOString().split("T")[0]; // YYYY-MM-DD
      if (!playtimeByDateAndGame[day]) {
        playtimeByDateAndGame[day] = {};
      }

      playtimeByDateAndGame[day][gameID] =
        (playtimeByDateAndGame[day][gameID] || 0) + seconds;
    });

    // 5. Extract unique game IDs and game names
    const games = new Map<number, Game>();
    this.games.forEach((g) => {
      games.set(g.id, g);
    });

    const uniqueGameIDs = Array.from(
      new Set(sessions.map((session) => session.gameID))
    );

    // 6. Format data for Chart.js
    const labels = allDatesInRange; // Dates (x-axis)
    const datasets = uniqueGameIDs.map((gameID) => ({
      label: `${games.get(gameID)!.name}`,
      data: labels.map((date) => {
        return (
          ((playtimeByDateAndGame[date] &&
            playtimeByDateAndGame[date][gameID]) ||
            0) / 3600
        ); // Convert seconds to hours
      }),
      backgroundColor: `${games.get(gameID)!.color}`, // Set specific game color
    }));

    return { labels, datasets };
  }

  getChart(): string {
    return `
      <canvas id="myChart"></canvas>
        <script>
        document.addEventListener("DOMContentLoaded", function () {
        fetch("/user/${this.userID}/chartData")
            .then(res => res.json())
            .then(data => {
                const ctx = document.getElementById("myChart").getContext("2d");
                new Chart(ctx, {
                    type: "bar",
                    data: {
                        labels: data.labels, // Dates
                        datasets: data.datasets // Games as datasets
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            title: {display: true, text: "Hours played"},
                            legend: { position: "top", display: false},
                        },
                        scales: {
                            x: { stacked: true }, // Stack bars by game
                            y: { stacked: true }
                        }
                    }
                });
            })
            .catch(err => console.error("Failed to load chart data:", err));
    });
        </script>`;
  }
}
