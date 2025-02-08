import { GLOBALS } from ".";
import { Game } from "./game";
import { Postgres } from "./postgres";
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
    const playtimeByDateAndGame: Record<string, Record<number, number>> = {};

    const games = new Map<number, Game>();
    for (const g of this.games) {
      games.set(g.id, g);
    }

    this.sessions.forEach(({ date, gameID, seconds }) => {
      const day = date.toISOString().split("T")[0]; // YYYY-MM-DD

      if (!playtimeByDateAndGame[day]) {
        playtimeByDateAndGame[day] = {}; // Create a new day entry
      }
      playtimeByDateAndGame[day][gameID] =
        (playtimeByDateAndGame[day][gameID] || 0) + seconds;
    });

    // Step 2: Extract unique game IDs
    const uniqueGameIDs = Array.from(
      new Set(this.sessions.map((session) => session.gameID))
    );

    // Step 3: Format data for Chart.js
    const labels = Object.keys(playtimeByDateAndGame); // Dates (x-axis)
    const datasets = uniqueGameIDs.map((gameID, index) => ({
      label: `${games.get(gameID)!.name}`,
      data: labels.map(
        (date) => (playtimeByDateAndGame[date][gameID] || 0) / 3600
      ), // Convert seconds to hours
      backgroundColor: `${games.get(gameID)!.color}`, // Generate different colors
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
