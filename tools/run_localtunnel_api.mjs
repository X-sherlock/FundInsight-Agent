import fs from "node:fs";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const localtunnel = require("C:/tmp/fundinsight-tunnel-node/node_modules/localtunnel");

const port = Number(process.env.PUBLIC_PROXY_PORT ?? 4173);
const urlFile = process.env.TUNNEL_URL_FILE ?? "C:/tmp/fundinsight-localtunnel-url.txt";
const logFile = process.env.TUNNEL_LOG_FILE ?? "C:/tmp/fundinsight-localtunnel-api.log";

function log(message) {
  fs.appendFileSync(logFile, `${new Date().toISOString()} ${message}\n`);
}

const tunnel = await localtunnel({
  port,
  local_host: "127.0.0.1",
});

fs.writeFileSync(urlFile, `${tunnel.url}\n`);
log(`url=${tunnel.url}`);

tunnel.on("close", () => log("closed"));
tunnel.on("error", (error) => log(`error=${error.message}`));

setInterval(() => {
  log("heartbeat");
}, 60000).unref();
