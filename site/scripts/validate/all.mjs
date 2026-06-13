/**
 * all.mjs — Run all validation scripts in sequence.
 * Imports and executes each stub; exits 0 when all pass.
 * Individual scripts add real assertions in plans 02-03..02-06.
 */
import './structure.mjs';
import './commune.mjs';
import './rollout.mjs';
import './hreflang.mjs';
import './schema.mjs';

console.log('all: validation suite complete (all stubs passed)');
