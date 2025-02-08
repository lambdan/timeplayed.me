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

  get totalPlaytime(): number {
    let sum = 0;
    for (const s of this.sessions) {
      sum += s.seconds;
    }
    return sum;
  }

  get lastActive(): Date {
    let latest = new Date(0);
    for (const s of this.sessions) {
      if (s.date.getTime() > latest.getTime()) {
        latest = s.date;
      }
    }
    return latest;
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
    allDatesInRange.push(today.toISOString().split("T")[0]); // and today

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
