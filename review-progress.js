(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.ReviewProgress = api;
}(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const FIELD_LABELS = {
    "间隔天数": "interval",
    "到期日期": "due",
    "复习次数": "reviews",
    "连续次数": "streak",
    "上次复习": "last",
    "更新时间": "updatedAt"
  };

  function normalizeWord(value) {
    return String(value || "")
      .replace(/^\d+\.\s*/, "")
      .replace(/[^\w\s-]/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  function normalizeReviewRecord(record = {}) {
    return {
      interval: Math.max(0, Number(record.interval) || 0),
      due: record.due || "",
      reviews: Math.max(0, Number(record.reviews) || 0),
      streak: Math.max(0, Number(record.streak) || 0),
      last: record.last || "",
      updatedAt: record.updatedAt || ""
    };
  }

  function reviewRecordTime(record) {
    const normalized = normalizeReviewRecord(record);
    const value = normalized.updatedAt || (normalized.last ? `${normalized.last}T00:00:00Z` : "");
    const time = Date.parse(value);
    return Number.isNaN(time) ? 0 : time;
  }

  function mergeReviewRecords(localRecords = {}, fileRecords = {}) {
    const merged = {};
    for (const [word, value] of Object.entries(localRecords)) {
      const key = normalizeWord(word);
      if (key) merged[key] = normalizeReviewRecord(value);
    }
    for (const [word, value] of Object.entries(fileRecords)) {
      const key = normalizeWord(word);
      if (!key) continue;
      const incoming = normalizeReviewRecord(value);
      if (!merged[key] || reviewRecordTime(incoming) >= reviewRecordTime(merged[key])) {
        merged[key] = incoming;
      }
    }
    return merged;
  }

  function parseReviewMarkdown(markdown) {
    const records = {};
    let word = "";
    for (const rawLine of String(markdown || "").replace(/\r\n/g, "\n").split("\n")) {
      const heading = rawLine.match(/^##\s+(.+?)\s*$/);
      if (heading) {
        word = normalizeWord(heading[1]);
        if (word) records[word] = normalizeReviewRecord(records[word]);
        continue;
      }
      if (!word) continue;
      const field = rawLine.match(/^-\s*([^：:]+)[：:]\s*(.*)$/);
      if (!field) continue;
      const key = FIELD_LABELS[field[1].trim()];
      if (!key) continue;
      records[word][key] = ["interval", "reviews", "streak"].includes(key)
        ? Number(field[2]) || 0
        : field[2].trim();
    }
    return records;
  }

  function serializeReviewMarkdown(records, exportedAt = new Date().toISOString()) {
    const normalizedRecords = mergeReviewRecords({}, records);
    const lines = [
      "# 回顾记录",
      "",
      "- 版本：1",
      `- 导出时间：${exportedAt}`,
      ""
    ];
    const words = Object.keys(normalizedRecords).sort((a, b) => a.localeCompare(b, "en"));
    for (const word of words) {
      const record = normalizedRecords[word];
      lines.push(
        `## ${word}`,
        "",
        `- 间隔天数：${record.interval}`,
        `- 到期日期：${record.due}`,
        `- 复习次数：${record.reviews}`,
        `- 连续次数：${record.streak}`,
        `- 上次复习：${record.last}`,
        `- 更新时间：${record.updatedAt}`,
        ""
      );
    }
    return `${lines.join("\n").trimEnd()}\n`;
  }

  return {
    mergeReviewRecords,
    normalizeReviewRecord,
    parseReviewMarkdown,
    reviewRecordTime,
    serializeReviewMarkdown
  };
}));
