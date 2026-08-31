const test = require("node:test");
const assert = require("node:assert/strict");

const {
  mergeReviewRecords,
  parseReviewMarkdown,
  serializeReviewMarkdown
} = require("../review-progress.js");

const older = {
  interval: 3,
  due: "2026-08-28",
  reviews: 2,
  streak: 2,
  last: "2026-08-25",
  updatedAt: "2026-08-25T08:00:00.000Z"
};

const newer = {
  interval: 8,
  due: "2026-09-02",
  reviews: 3,
  streak: 3,
  last: "2026-08-25",
  updatedAt: "2026-08-25T09:00:00.000Z"
};

test("parses the standard Markdown field format", () => {
  const markdown = `# 回顾记录\r\n\r\n## access\r\n\r\n- 间隔天数：3\r\n- 到期日期：2026-08-28\r\n- 复习次数：2\r\n- 连续次数：2\r\n- 上次复习：2026-08-25\r\n- 更新时间：2026-08-25T08:00:00.000Z\r\n`;
  assert.deepEqual(parseReviewMarkdown(markdown), { access: older });
});

test("serialization round-trip preserves every historical word", () => {
  const records = { access: older, memory: newer };
  const markdown = serializeReviewMarkdown(records, "2026-08-25T10:00:00.000Z");
  assert.deepEqual(parseReviewMarkdown(markdown), records);
});

test("merge keeps untouched words and selects the newest record per word", () => {
  const local = { access: newer, memory: older };
  const file = { access: older, location: newer };
  assert.deepEqual(mergeReviewRecords(local, file), {
    access: newer,
    memory: older,
    location: newer
  });
});

test("unknown metadata does not become a review field", () => {
  const markdown = `# 回顾记录\n\n- 版本：1\n\n## signal\n\n- 未知字段：ignored\n- 复习次数：4\n`;
  assert.deepEqual(parseReviewMarkdown(markdown).signal, {
    interval: 0,
    due: "",
    reviews: 4,
    streak: 0,
    last: "",
    updatedAt: ""
  });
});
