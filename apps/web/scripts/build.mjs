import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

function deriveVersion() {
  const sha = process.env.VERCEL_GIT_COMMIT_SHA ?? process.env.NEXT_PUBLIC_APP_VERSION;
  if (sha) {
    return sha;
  }

  const gitSha = spawnSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' });
  if (gitSha.status === 0) {
    return gitSha.stdout.trim();
  }

  return 'dev';
}

const version = deriveVersion();
const versionLabel = version === 'dev' ? 'dev' : version.slice(0, 7);
const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const appDir = path.resolve(scriptDir, '..');
const localNextBin = path.join(appDir, 'node_modules', '.bin', process.platform === 'win32' ? 'next.cmd' : 'next');
const nextCommand = existsSync(localNextBin) ? localNextBin : process.platform === 'win32' ? 'npx.cmd' : 'npx';
const nextArgs = existsSync(localNextBin) ? ['build'] : ['next', 'build'];

const result = spawnSync(nextCommand, nextArgs, {
  stdio: 'inherit',
  shell: false,
  cwd: appDir,
  env: {
    ...process.env,
    NEXT_PUBLIC_APP_VERSION: process.env.NEXT_PUBLIC_APP_VERSION ?? version,
    NEXT_PUBLIC_APP_VERSION_LABEL: process.env.NEXT_PUBLIC_APP_VERSION_LABEL ?? versionLabel,
    NEXT_PUBLIC_BUILD_UPDATED_AT: process.env.NEXT_PUBLIC_BUILD_UPDATED_AT ?? new Date().toISOString(),
    NEXT_PUBLIC_BUILD_DEPLOYMENT_ID:
      process.env.NEXT_PUBLIC_BUILD_DEPLOYMENT_ID ?? process.env.VERCEL_DEPLOYMENT_ID ?? '',
  },
});

process.exit(result.status ?? 1);
