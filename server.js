// Zero-dependency static server for dist/ (used by `npm start` on AnySites).
"use strict";

const http = require("http");
const fs = require("fs");
const path = require("path");
const zlib = require("zlib");

const PORT = parseInt(process.env.PORT, 10) || 3000;
const ROOT = path.join(__dirname, "dist");

const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".svg": "image/svg+xml",
  ".xml": "application/xml; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".webp": "image/webp",
  ".ico": "image/x-icon",
};
const COMPRESSIBLE = new Set([".html", ".css", ".js", ".svg", ".xml", ".txt", ".json"]);

const NOT_FOUND = `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex">
<title>Page not found | Peptide Calculator</title><link rel="stylesheet" href="/assets/style.css"></head>
<body><main class="wrap"><section class="hero"><h1>Page not found</h1>
<p class="lead">That page does not exist. Try the <a href="/">peptide calculator</a>,
the <a href="/peptide-reconstitution-calculator/">reconstitution calculator</a> or the
<a href="/peptide-dosage-calculator/">dosage calculator</a>.</p></section></main></body></html>`;

function send(req, res, status, headers, body, ext) {
  const accepts = req.headers["accept-encoding"] || "";
  if (COMPRESSIBLE.has(ext) && body.length > 1024 && /\bgzip\b/.test(accepts)) {
    body = zlib.gzipSync(body);
    headers["Content-Encoding"] = "gzip";
  }
  headers["Vary"] = "Accept-Encoding";
  headers["Content-Length"] = body.length;
  headers["X-Content-Type-Options"] = "nosniff";
  res.writeHead(status, headers);
  res.end(req.method === "HEAD" ? undefined : body);
}

function redirect(res, location) {
  res.writeHead(301, { Location: location, "Content-Length": 0 });
  res.end();
}

const server = http.createServer((req, res) => {
  if (req.method !== "GET" && req.method !== "HEAD") {
    res.writeHead(405, { Allow: "GET, HEAD" });
    return res.end();
  }

  // www -> apex, one canonical host
  const host = (req.headers.host || "").toLowerCase();
  if (host.startsWith("www.")) return redirect(res, "https://" + host.slice(4) + req.url);

  let url;
  try {
    url = new URL(req.url, "http://localhost");
  } catch {
    res.writeHead(400);
    return res.end();
  }
  let pathname;
  try {
    pathname = decodeURIComponent(url.pathname);
  } catch {
    res.writeHead(400);
    return res.end();
  }

  let file = path.normalize(path.join(ROOT, pathname));
  if (file !== ROOT && !file.startsWith(ROOT + path.sep)) {
    res.writeHead(403);
    return res.end();
  }

  let stat = fs.statSync(file, { throwIfNoEntry: false });
  if (stat && stat.isDirectory()) {
    // canonical URLs end in a slash; /foo -> /foo/
    if (!pathname.endsWith("/")) return redirect(res, pathname + "/" + url.search);
    file = path.join(file, "index.html");
    stat = fs.statSync(file, { throwIfNoEntry: false });
  }

  if (!stat || !stat.isFile()) {
    return send(req, res, 404, { "Content-Type": TYPES[".html"], "Cache-Control": "no-cache" },
      Buffer.from(NOT_FOUND), ".html");
  }

  const ext = path.extname(file).toLowerCase();
  const headers = { "Content-Type": TYPES[ext] || "application/octet-stream" };
  if (ext === ".html") headers["Cache-Control"] = "no-cache";
  else if (url.searchParams.has("v")) headers["Cache-Control"] = "public, max-age=31536000, immutable";
  else headers["Cache-Control"] = "public, max-age=86400";

  send(req, res, 200, headers, fs.readFileSync(file), ext);
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`Peptide calculator serving ${ROOT} on port ${PORT}`);
});
