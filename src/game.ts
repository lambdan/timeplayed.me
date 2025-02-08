import { Session } from "./session";
import { User } from "./user";
import { colorFromString } from "./utils";

export interface GameStatsForPlayer {
  seconds: number;
  lastPlayed: Date;
  longestSession: Session;
  sessions: Session[];
}

export class Game {
  readonly id: number;
  readonly name: string;
  readonly sessions: Session[];
  constructor(id: number, name: string, sessions: Session[]) {
    this.id = id;
    this.name = name;
    this.sessions = sessions;
  }

  get lastPlayed(): Date {
    let latest = new Date(0);
    for (const s of this.sessions) {
      if (s.date.getTime() > latest.getTime()) {
        latest = s.date;
      }
    }
    return latest;
  }

  get totalSessions(): number {
    return this.sessions.length;
  }

  get totalPlaytime(): number {
    let sum = 0;
    for (const s of this.sessions) {
      sum += s.seconds;
    }
    return sum;
  }

  get color(): string {
    return colorFromString(this.name);
  }

  /**
   * Returns user IDs that have played this game
   */
  get players(): string[] {
    let userIds = new Set<string>();
    for (const s of this.sessions) {
      userIds.add(s.userID);
    }
    return [...userIds];
  }

  getGameStatsForUser(userID: string): GameStatsForPlayer {
    const playerSessions: Session[] = [];
    for (const s of this.sessions) {
      if (s.userID === userID) {
        playerSessions.push(s);
      }
    }
    let lastPlayed = new Date(0);
    let totalPlayed = 0;
    let longestSession = playerSessions[0];
    for (const s of playerSessions) {
      totalPlayed += s.seconds;
      if (s.date.getTime() > lastPlayed.getTime()) {
        lastPlayed = s.date;
      }
      if (s.seconds > longestSession.seconds) {
        longestSession = s;
      }
    }
    return {
      seconds: totalPlayed,
      lastPlayed: lastPlayed,
      sessions: playerSessions,
      longestSession: longestSession,
    };
  }

  chartData() {
    const sessions = [...this.sessions].reverse();
    const playtimeByDate: Record<string, number> = {};
    // Fill in blank days
    const first = sessions[0].date;
    const today = new Date();
    let now = first;
    while (now.getTime() < today.getTime()) {
      const day = now.toISOString().split("T")[0];
      playtimeByDate[day] = 0;
      now = new Date(now.getTime() + 86400 * 1000);
    }
    playtimeByDate[today.toISOString().split("T")[0]] = 0;

    // Add session data
    sessions.forEach(({ date, seconds }) => {
      const day = date.toISOString().split("T")[0]; // Convert Date to YYYY-MM-DD string
      playtimeByDate[day] = playtimeByDate[day] + seconds;
    });

    return {
      labels: Object.keys(playtimeByDate),
      values: Object.values(playtimeByDate).map((sec) => sec / 3600),
    };
  }

  getChart(): string {
    return `
      <canvas id="myChart"></canvas>
        <script>
        document.addEventListener("DOMContentLoaded", function () {
        if (typeof Chart === "undefined") {
            console.error("Chart.js failed to load.");
            return;
        }

        fetch("/game/${this.id}/chartData")
            .then(res => res.json())
            .then(data => {
                const ctx = document.getElementById("myChart").getContext("2d");
                new Chart(ctx, {
                    type: "bar",
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: "Hours Played per Day",
                            data: data.values,
                            backgroundColor: "rgba(75, 192, 192, 0.5)",
                        }]
                    }
                });
            })
            .catch(err => console.error("Failed to load chart data:", err));
    });
        </script>`;
  }
}
