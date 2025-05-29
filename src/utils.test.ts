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
    const dayAgo = new Date(Date.now() - 86400000); // 1 day ago
    assert.strictEqual(utils.timeSince(dayAgo), "1 day(s) ago");

    const hourAgo = new Date(Date.now() - 3600000); // 1 hour ago
    assert.strictEqual(utils.timeSince(hourAgo), "1 hour(s) ago");

    const minuteAgo = new Date(Date.now() - 60000); // 1 minute ago
    assert.strictEqual(utils.timeSince(minuteAgo), "1 min(s) ago");

    const justNow = new Date(Date.now() - 1000); // just now
    assert.strictEqual(utils.timeSince(justNow), "just now");
  });

  test("Format seconds", () => {
    assert.strictEqual(utils.formatSeconds(3600), "1.0 hr(s)");
    assert.strictEqual(utils.formatSeconds(7200), "2.0 hr(s)");
    assert.strictEqual(utils.formatSeconds(120), "2 min(s)");
    assert.strictEqual(utils.formatSeconds(60), "1 min(s)");
    assert.strictEqual(utils.formatSeconds(30), "<1 min");
    assert.strictEqual(utils.formatSeconds(86400 * 2, 1), "2 days");
  });

  test("Sanitize HTML", () => {
    assert.strictEqual(utils.sanitizeHTML('<<<>>>'), '');

  });
});
