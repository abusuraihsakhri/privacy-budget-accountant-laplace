const test = require('node:test');
const assert = require('node:assert/strict');
const { createLedger, sensitivityFor, laplace } = require('../web/app.js');

test('Laplace inverse CDF is correct at fixed quantiles', () => {
  assert.ok(Math.abs(laplace(2, 0.25) + 2 * Math.log(2)) < 1e-12);
  assert.equal(laplace(2, 0.5), 0);
  assert.ok(Math.abs(laplace(2, 0.75) - 2 * Math.log(2)) < 1e-12);
});

test('sensitivity is tied to query adjacency', () => {
  assert.equal(sensitivityFor('count', {}), 1);
  assert.equal(sensitivityFor('mean', { lower: 0, upper: 100, n: 50 }), 2);
  assert.throws(() => sensitivityFor('mean', { lower: 20, upper: 10, n: 4 }));
  assert.throws(() => sensitivityFor('mean', { lower: 0, upper: 1, n: 0 }));
});

test('budget rejects overspending without charging a failed release', () => {
  const ledger = createLedger(0.3);
  ledger.release(5, 0.1, 1);
  ledger.release(10, 0.2, 1);
  assert.ok(Math.abs(ledger.spent - 0.3) < 1e-12);
  assert.throws(() => ledger.release(10, 0.1, 1), /Insufficient/);
  assert.equal(ledger.remaining, 0);
  assert.throws(() => ledger.release(10, Number.NaN, 1));
});

test('invalid data and noise scales fail closed', () => {
  assert.throws(() => createLedger(0));
  assert.throws(() => laplace(0, 0.5));
  assert.throws(() => laplace(1, 0));
  assert.throws(() => createLedger(1).release(5, 0.2, 0));
});
