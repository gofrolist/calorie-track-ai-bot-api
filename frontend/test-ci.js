#!/usr/bin/env node

import { spawn } from 'child_process';

const testProcess = spawn('npx', ['vitest', 'run'], {
  stdio: 'inherit'
});

testProcess.on('close', (code) => {
  process.exit(code ?? 1);
});

testProcess.on('error', (error) => {
  console.error('Test process error:', error);
  process.exit(1);
});
