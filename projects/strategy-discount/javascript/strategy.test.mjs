import assert from "node:assert/strict";
import { checkout, strategies } from "./strategy.mjs";

assert.equal(checkout(12_500, strategies.none), 12_500);
assert.equal(checkout(12_500, strategies.seasonal), 11_250);
assert.equal(checkout(12_500, strategies.vip), 10_000);
assert.throws(() => checkout(-1, strategies.none), /positive/);

console.log("ok");

