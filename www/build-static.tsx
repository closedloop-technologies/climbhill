import { cp, mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { renderToStream } from "remix/ui/server";
import { Home } from "./app/home.tsx";

const output = join(process.cwd(), "dist");
await mkdir(join(output, "assets"), { recursive: true });
const html = await new Response(renderToStream(<Home />)).text();
await writeFile(join(output, "index.html"), `<!doctype html>${html}\n`);
await writeFile(join(output, "CNAME"), "climbhill.ai\n");
await writeFile(join(output, ".nojekyll"), "");
await cp(join(process.cwd(), "..", "assets", "hero-research-harness.png"), join(output, "assets", "hero-research-harness.png"));
