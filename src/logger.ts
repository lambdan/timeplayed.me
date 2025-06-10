export class Logger {
  identifier: string;
  verbose: boolean = false;

  constructor(identifier: string) {
    this.identifier = identifier;
    this.verbose = process.env.NODE_ENV !== "production";
  }

  date(): string {
    return new Date().toISOString();
  }

  log(...messages: any[]) {
    console.log(`${this.date()} [${this.identifier}]`, ...messages);
  }

  warn(...messages: any[]) {
    console.warn(`${this.date()} [${this.identifier}]`, ...messages);
  }

  error(...messages: any[]) {
    console.error(`${this.date()} [${this.identifier}]`, ...messages);
  }

  debug(...messages: any[]) {
    if (this.verbose) {
      console.debug(`${this.date()} [${this.identifier}]`, ...messages);
    }
  }
}
