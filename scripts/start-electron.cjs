const { spawn } = require("node:child_process");
const electronPath = require("electron");

const env = { ...process.env };
const isDev = process.argv.includes("--dev");

delete env.ELECTRON_RUN_AS_NODE;

if (isDev) {
  env.VITE_DEV_SERVER_URL = "http://127.0.0.1:5173";
} else {
  delete env.VITE_DEV_SERVER_URL;
}

const child = spawn(electronPath, ["."], {
  cwd: process.cwd(),
  env,
  stdio: "inherit",
  windowsHide: false
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }

  process.exit(code ?? 0);
});
