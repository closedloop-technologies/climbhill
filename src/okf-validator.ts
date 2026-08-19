import { readFile, readdir } from "node:fs/promises";
import { join } from "node:path";
import { parseFrontmatter } from "./io.js";

export async function validateOkf(root: string): Promise<{ concepts: number; errors: string[] }> {
  const okf = join(root, "research", "okf");
  const errors: string[] = [];
  let concepts = 0;
  async function visit(directory: string): Promise<void> {
    for (const entry of await readdir(directory, { withFileTypes: true })) {
      const path = join(directory, entry.name);
      if (entry.isDirectory()) await visit(path);
      else if (entry.name.endsWith(".md") && !["index.md", "log.md"].includes(entry.name)) {
        concepts += 1;
        try {
          const content = await readFile(path, "utf8");
          if (content.includes("\uFFFD")) throw new Error("file is not valid UTF-8");
          const { data } = parseFrontmatter<Record<string, unknown>>(content);
          if (typeof data.type !== "string" || !data.type.trim()) errors.push(`${path}: non-empty type is required`);
        } catch (error) { errors.push(`${path}: ${error instanceof Error ? error.message : String(error)}`); }
      }
    }
  }
  await visit(okf);
  return { concepts, errors };
}
