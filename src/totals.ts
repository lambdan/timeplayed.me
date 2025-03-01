import { STATICS } from ".";
import { Logger } from "./logger";
import { colorFromString } from "./utils";

export class Totals {
  private logger = new Logger("Postgres");
  constructor() {}

  async lastPlayed(): Promise<Date> {
    const sessions = await STATICS.pg.fetchSessions();
    let latest = new Date(0);
    for (const s of sessions) {
      if (s.date.getTime() > latest.getTime()) {
        latest = s.date;
      }
    }
    return latest;
  }

  async totalSessions(): Promise<number> {
    const sessions = await STATICS.pg.fetchSessions();
    return sessions.length;
  }

  async totalPlaytime(): Promise<number> {
    const sessions = await STATICS.pg.fetchSessions();
    let sum = 0;
    for (const s of sessions) {
      sum += s.seconds;
    }
    return sum;
  }

  get color(): string {
    return colorFromString("TOTAL");
  }

  async chartData() {
    const sessions = (await STATICS.pg.fetchSessions()).reverse();
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
    // Add today if its not in there
    const todayString = today.toISOString().split("T")[0];
    if (!playtimeByDate[todayString]) {
      playtimeByDate[todayString] = 0;
    }

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

        fetch("/totals/chartData")
            .then(res => res.json())
            .then(data => {
                const ctx = document.getElementById("myChart").getContext("2d");
                new Chart(ctx, {
                    type: "bar",
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: "Hours Played",
                            data: data.values,
                            backgroundColor: "${this.color}",
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            title: {display: true, text: "Hours tracked"},
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
