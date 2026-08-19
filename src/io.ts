import { createHash, randomUUID } from "node:crypto";
import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import { dirname } from "node:path";
import * as YAML from "yaml";

export function hash(value: string | Buffer): string {
  return createHash("sha256").update(value).digest("hex");
}

export function shortId(): string {
  return randomUUID().replaceAll("-", "").slice(0, 12);
}

export function now(): string {
  return new Date().toISOString();
}

export async function atomicWrite(path: string, content: string | Buffer): Promise<void> {
  await mkdir(dirname(path), { recursive: true });
  const temporary = `${path}.tmp-${process.pid}-${randomUUID()}`;
  await writeFile(temporary, content);
  await rename(temporary, path);
}

export async function readYaml<T>(path: string): Promise<T> {
  return YAML.parse(await readFile(path, "utf8")) as T;
}

export async function writeYaml(path: string, value: unknown): Promise<void> {
  await atomicWrite(path, YAML.stringify(value, { lineWidth: 0 }));
}

export function frontmatter(value: Record<string, unknown>, body: string): string {
  return `---\n${YAML.stringify(value, { lineWidth: 0 }).trim()}\n---\n\n${body.trim()}\n`;
}

export function parseFrontmatter<T>(content: string): { data: T; body: string } {
  if (!content.startsWith("---\n")) throw new Error("OKF concept is missing YAML frontmatter");
  const end = content.indexOf("\n---\n", 4);
  if (end < 0) throw new Error("OKF concept has unterminated YAML frontmatter");
  return { data: YAML.parse(content.slice(4, end)) as T, body: content.slice(end + 5).trim() };
}

export async function writeConcept(path: string, data: Record<string, unknown>, body: string): Promise<void> {
  let merged = data;
  try {
    const existing = parseFrontmatter<Record<string, unknown>>(await readFile(path, "utf8")).data;
    merged = { ...existing, ...data };
  } catch { /* new concept */ }
  await atomicWrite(path, frontmatter(merged, body));
}
