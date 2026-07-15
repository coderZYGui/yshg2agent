import assert from "node:assert/strict";

import { getPastedFiles } from "../src/utils/getPastedFiles.ts";

const image = { name: "paste.png" };
const document = { name: "review.pdf" };
const files = getPastedFiles([
  { kind: "string", getAsFile: () => null },
  { kind: "file", getAsFile: () => image },
  { kind: "file", getAsFile: () => document },
]);

assert.deepEqual(files, [image, document]);
