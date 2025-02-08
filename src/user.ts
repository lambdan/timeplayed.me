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
    const playtimeByDate: Record<string, number> = {};
    this.sessions.forEach(({ date, seconds }) => {
      const day = date.toISOString().split("T")[0]; // Convert Date to YYYY-MM-DD string
      playtimeByDate[day] = (playtimeByDate[day] || 0) + seconds;
    });
    return {
      labels: Object.keys(playtimeByDate), // Dates as strings
      values: Object.values(playtimeByDate).map((sec) => sec / 3600), // Convert seconds to hours
    };
  }

  getChart(): string {
    return `
      <canvas id="myChart"></canvas>
        <script>
        document.addEventListener("DOMContentLoaded", function () {
        fetch("/user/${this.userID}/chart")
            .then(res => res.json())
            .then(data => {
                const ctx = document.getElementById("myChart").getContext("2d");
                new Chart(ctx, {
                    type: "bar",
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: "Hours played",
                            data: data.values,
                            backgroundColor: "rgba(0, 255, 140, 0.5)",
                        }]
                    }
                });
            });
    });</script>`;
  }
}
