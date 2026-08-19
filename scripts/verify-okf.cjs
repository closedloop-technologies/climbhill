const { createHash } = require("node:crypto");
const { readFileSync } = require("node:fs");
const { join } = require("node:path");
const YAML = require("yaml");

const root = join(__dirname, "..", "docs", "specifications", "okf-v0.2");
const manifest = YAML.parse(readFileSync(join(root, "PROVENANCE.yaml"), "utf8"));
if (manifest.version !== "0.2" || !manifest.upstream_commit || manifest.license !== "Apache-2.0") throw new Error("invalid OKF provenance manifest");
for (const file of manifest.files) {
  const digest = createHash("sha256").update(readFileSync(join(root, file.path))).digest("hex");
  if (digest !== file.sha256) throw new Error(`${file.path}: expected ${file.sha256}, received ${digest}`);
}
console.log(`Verified OKF ${manifest.version} at ${manifest.upstream_commit}`);
