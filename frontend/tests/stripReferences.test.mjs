import assert from "node:assert/strict";

import { stripReferenceTags } from "../src/utils/stripReferences.ts";

assert.equal(
  stripReferenceTags("结论<ref>[2][3]</ref>，请继续。"),
  "结论，请继续。"
);
assert.equal(stripReferenceTags("没有引用标记。"), "没有引用标记。");
