import { describe, test } from "node:test";
import { strict as assert } from "node:assert";
import * as utils from "./utils";

describe("Utils", () => {
  test("Clamp", () => {
    assert.strictEqual(utils.clamp(5, 1, 10), 5);
    assert.strictEqual(utils.clamp(0, 1, 10), 1);
    assert.strictEqual(utils.clamp(15, 1, 10), 10);
  });

  test("Time since", () => {
    const SECOND = 1000;
    const MINUTE = 60 * SECOND;
    const HOUR = 60 * MINUTE;
    const DAY = 24 * HOUR;
    const YEAR = 365 * DAY;
    const halfMinuteAgo = new Date(Date.now() - 0.5 * MINUTE);
    const oneAndHalfMinutesAgo = new Date(Date.now() - 1.5 * MINUTE);
    const oneHourAgo = new Date(Date.now() - HOUR);
    const oneAndHalfHourAgo = new Date(Date.now() - 1.5 * HOUR);
    const tenHoursAgo = new Date(Date.now() - 10 * HOUR);
    const oneDayAgo = new Date(Date.now() - DAY);
    const tenDaysAgo = new Date(Date.now() - 10 * DAY);
    const oneYearAgo = new Date(Date.now() - YEAR);
    const twoYearsAgo = new Date(Date.now() - 2 * YEAR);
    const tenYearsAgo = new Date(Date.now() - 10 * YEAR);
    assert.strictEqual(utils.timeSince(halfMinuteAgo), "just now");
    assert.strictEqual(utils.timeSince(oneAndHalfMinutesAgo), "1 minute ago");
    assert.strictEqual(utils.timeSince(oneHourAgo), "1 hour ago");
    assert.strictEqual(utils.timeSince(oneAndHalfHourAgo), "1 hour ago");
    assert.strictEqual(utils.timeSince(tenHoursAgo), "10 hours ago");
    assert.strictEqual(utils.timeSince(oneDayAgo), "1 day ago");
    assert.strictEqual(utils.timeSince(tenDaysAgo), "10 days ago");
    assert.strictEqual(utils.timeSince(oneYearAgo), "1 year ago");
    assert.strictEqual(utils.timeSince(twoYearsAgo), "2 years ago");
    assert.strictEqual(utils.timeSince(tenYearsAgo), "10 years ago");
  });

  test("Format seconds", () => {
    const SECOND = 1;
    const MINUTE = 60 * SECOND;
    const HOUR = 60 * MINUTE;
    const DAY = 24 * HOUR;
    const YEAR = 365 * DAY;
    assert.strictEqual(utils.formatSeconds(MINUTE), "1 minute");
    assert.strictEqual(utils.formatSeconds(2 * MINUTE), "2 minutes");
    assert.strictEqual(utils.formatSeconds(HOUR), "1 hour");
    assert.strictEqual(utils.formatSeconds(1.5 * HOUR), "1.5 hours");
    assert.strictEqual(utils.formatSeconds(2 * HOUR), "2.0 hours");
    assert.strictEqual(utils.formatSeconds(DAY), "24.0 hours");
    assert.strictEqual(utils.formatSeconds(2 * DAY), "48.0 hours");
    assert.strictEqual(utils.formatSeconds(2 * DAY, 1), "2 days");
    assert.strictEqual(utils.formatSeconds(YEAR), "8760.0 hours");
    assert.strictEqual(utils.formatSeconds(2 * YEAR), "17520.0 hours");
    assert.strictEqual(utils.formatSeconds(YEAR, 1), "365 days");
    assert.strictEqual(utils.formatSeconds(YEAR * 2, 2), "730 days");
  });

  test("Sanitize HTML", () => {
    assert.strictEqual(utils.sanitizeHTML("<<<>>>"), "");
  });
});
