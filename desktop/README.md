# CKD-CI Desktop Wrapper

This folder contains the Electron wrapper for the CKD-CI web app.

## Run in dev mode

From repository root:

npm run desktop

or:

npm run desktop:dev

This opens Electron and points it to:

http://localhost:3000

Make sure frontend dev server is running first.

## Run desktop + frontend in one command

From repository root:

npm run desktop:up

What it does:

1. Starts backend on port 8000 in a new terminal (if not already running).
2. Waits for http://localhost:8000/health.
3. Starts frontend on port 3000 in a new terminal (if not already running).
4. Waits until http://localhost:3000 is reachable.
5. Starts Electron desktop in a new terminal.

This avoids startup race conditions where Electron opens before Next.js is ready.

## Production target URL

Desktop app production URL is configured in:

./electron/config.json

Field:

productionUrl

Example:

{
  "productionUrl": "https://your-web-host.example.com"
}

## Build Windows exe installer

From repository root:

npm run desktop:build

To build and automatically copy the latest installer to your Windows Desktop:

npm run desktop:build:desktop

Note for Windows permission issues:

If you see a winCodeSign extraction error about symbolic links, the build config already disables signing/editing for local builds.
If your machine still blocks it, run the terminal as Administrator once or enable Windows Developer Mode and retry.

Output files are generated in:

./desktop/dist

Typical output:

- NSIS installer exe
- unpacked app folder

## Suggested release flow

1. Build and deploy web app backend/frontend first.
2. Set productionUrl in ./desktop/electron/config.json.
3. Run npm run desktop:build.
4. Distribute installer exe from ./desktop/dist.
