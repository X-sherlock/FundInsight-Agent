import { spawn } from "node:child_process";
import fs from "node:fs";

const borePath = process.env.BORE_PATH ?? "C:/tmp/bore/bore.exe";
const localPort = process.env.PUBLIC_PROXY_PORT ?? "4173";
const urlFile = process.env.BORE_URL_FILE ?? "C:/tmp/fundinsight-bore-url.txt";
const logFile = process.env.BORE_LOG_FILE ?? "C:/tmp/fundinsight-bore.log";

fs.rmSync(urlFile, { force: true });

function append(data) {
  const text = data.toString();
  fs.appendFileSync(logFile, text);
  const match = text.match(/bore\.pub:(\d+)/);
  if (match) {
    fs.writeFileSync(urlFile, `http://bore.pub:${match[1]}\n`);
  }
}

const child = spawn(borePath, ["local", localPort, "--to", "bore.pub"], {
  stdio: ["ignore", "pipe", "pipe"],
  windowsHide: true,
});

fs.writeFileSync("C:/tmp/fundinsight-bore.pid", String(process.pid));
child.stdout.on("data", append);
child.stderr.on("data", append);
child.on("exit", (code, signal) => {
  fs.appendFileSync(logFile, `\n[bore exited code=${code} signal=${signal}]\n`);
  process.exit(code ?? 1);
});
