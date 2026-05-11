import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const npxPath = process.env.NPX_PATH ?? "D:\\Software\\NodeJs\\npx.cmd";
const port = process.env.PUBLIC_PROXY_PORT ?? "4173";
const logDir = process.env.TUNNEL_LOG_DIR ?? "C:\\tmp";

fs.mkdirSync(logDir, { recursive: true });
const out = fs.openSync(path.join(logDir, "fundinsight-tunnel.out.log"), "a");
const err = fs.openSync(path.join(logDir, "fundinsight-tunnel.err.log"), "a");

const child = spawn(
  npxPath,
  ["-y", "localtunnel", "--port", port, "--local-host", "127.0.0.1"],
  {
    cwd: root,
    detached: true,
    shell: true,
    stdio: ["ignore", out, err],
    windowsHide: true,
  },
);

child.unref();
fs.writeFileSync(path.join(logDir, "fundinsight-tunnel.pid"), String(child.pid));
console.log(`Started localtunnel PID ${child.pid} for http://127.0.0.1:${port}`);
