import test from 'node:test';
import assert from 'node:assert/strict';
import { concentration, volume, convert, positive } from '../assets/bac-water.mjs';

test('concentration and both output units', () => {
  const result = concentration(5, 2);
  assert.equal(result.value, 2.5);
  assert.equal(result.secondary, '2,500 mcg/mL');
  assert.match(result.formula, /5 mg ÷ 2 mL = 2.5 mg\/mL/);
});
test('theoretical volume', () => {
  assert.equal(volume(5, 2.5).value, 2);
  assert.match(volume(5, 2.5).formula, /theoretical/);
});
test('both directions of both unit families', () => {
  assert.equal(convert(1, 'mg').value, 1000);
  assert.equal(convert(1000, 'mcg').value, 1);
  assert.equal(convert(1, 'mL').value, 1000);
  assert.equal(convert(1000, 'uL').value, 1);
});
test('input boundaries and errors', () => {
  for (const raw of ['', ' ', '0', '-1', 'Infinity', 'NaN', '1e999']) assert.equal(positive(raw), null);
  assert.equal(positive('0.0001'), 0.0001);
  assert.throws(() => concentration(1, 0), RangeError);
  assert.throws(() => volume(1, -1), RangeError);
  assert.throws(() => convert(Infinity, 'mg'), RangeError);
  assert.throws(() => concentration(Number.MAX_VALUE, 0.1), RangeError);
});
