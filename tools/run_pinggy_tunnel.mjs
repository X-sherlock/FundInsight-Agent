import { spawn } from "node:child_process";
import fs from "node:fs";

const localPort = process.env.PUBLIC_PROXY_PORT ?? "4173";
const urlFile = process.env.PINGGY_URL_FILE ?? "C:/tmp/fundinsight-pinggy-url.txt";
const logFile = process.env.PINGGY_LOG_FILE ?? "C:/tmp/fundinsight-pinggy.log";

fs.rmSync(urlFile, { force: true });
fs.rmSync(logFile, { force: true });

function append(data) {
  const text = data.toString();
  fs.appendFileSync(logFile, text);
  const match = text.match(/https?:\/\/[^\s"'<>]+/);
  if (match && match[0].includes("pinggy")) {
    fs.writeFileSync(urlFile, `${match[0]}\n`);
  }
}

const child = spawn(
  "C:/Windows/System32/OpenSSH/ssh.exe",
  [
    "-p",
    "443",
    "-o",
    "StrictHostKeyChecking=no",
    "-o",
    "UserKnownHostsFile=C:/tmp/fundinsight-pinggy-known-hosts",
    "-o",
    "ServerAliveInterval=30",
    "-R",
    `0:127.0.0.1:${localPort}`,
    "free.pinggy.io",
  ],
  {
    stdio: ["pipe", "pipe", "pipe"],
    windowsHide: true,
  },
);

fs.writeFileSync("C:/tmp/fundinsight-pinggy.pid", String(process.pid));
setInterval(() => {
  child.stdin.write("\n");
}, 2000).unref();
child.stdout.on("data", append);
child.stderr.on("data", append);
child.on("exit", (code, signal) => {
  fs.appendFileSync(logFile, `\n[ssh exited code=${code} signal=${signal}]\n`);
  process.exit(code ?? 1);
});
