import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const distRoot = path.join(root, "frontend", "dist");
const apiTarget = new URL(process.env.FUNDINSIGHT_API_TARGET ?? "http://127.0.0.1:8000");
const port = Number(process.env.PUBLIC_PROXY_PORT ?? 4173);

const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".ico": "image/x-icon",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".map": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".txt": "text/plain; charset=utf-8",
  ".webp": "image/webp",
};

const server = http.createServer((req, res) => {
  if (!req.url) {
    res.writeHead(400).end("Bad Request");
    return;
  }

  if (req.url.startsWith("/api/")) {
    proxyApi(req, res);
    return;
  }

  serveStatic(req, res);
});

function proxyApi(req, res) {
  const targetUrl = new URL(req.url ?? "/", apiTarget);
  const proxyReq = http.request(
    targetUrl,
    {
      method: req.method,
      headers: {
        ...req.headers,
        host: apiTarget.host,
      },
    },
    (proxyRes) => {
      res.writeHead(proxyRes.statusCode ?? 502, proxyRes.headers);
      proxyRes.pipe(res);
    },
  );

  proxyReq.on("error", (error) => {
    res.writeHead(502, { "content-type": "application/json; charset=utf-8" });
    res.end(JSON.stringify({ detail: { code: "API_PROXY_FAILED", message: error.message } }));
  });

  req.pipe(proxyReq);
}

function serveStatic(req, res) {
  const requestPath = decodeURIComponent(new URL(req.url ?? "/", "http://localhost").pathname);
  const relativePath = requestPath === "/" ? "index.html" : requestPath.replace(/^\/+/, "");
  let filePath = path.resolve(distRoot, relativePath);

  if (!filePath.startsWith(distRoot)) {
    res.writeHead(403).end("Forbidden");
    return;
  }

  if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
    filePath = path.join(distRoot, "index.html");
  }

  const ext = path.extname(filePath).toLowerCase();
  res.setHeader("content-type", contentTypes[ext] ?? "application/octet-stream");

  if (ext === ".js") {
    const source = fs.readFileSync(filePath, "utf8");
    const rewritten = source.replace(
      'const I2=tb("http://127.0.0.1:8000");',
      "const I2=window.location.origin;",
    );
    res.writeHead(200);
    res.end(rewritten);
    return;
  }

  fs.createReadStream(filePath)
    .on("error", () => res.writeHead(500).end("Static file read failed"))
    .pipe(res);
}

server.listen(port, "127.0.0.1", () => {
  console.log(`FundInsight public proxy listening on http://127.0.0.1:${port}`);
});
