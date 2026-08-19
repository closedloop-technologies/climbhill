import { execFile } from "node:child_process";
import { access, readFile, readdir } from "node:fs/promises";
import { basename, extname, join, resolve } from "node:path";
import { promisify } from "node:util";
import { fetchTranscript } from "youtube-transcript";
import { atomicWrite, frontmatter, hash, now, parseFrontmatter, writeConcept } from "./io.js";
import type { ResourceVersion, SourceType } from "./types.js";

const execFileAsync = promisify(execFile);

export interface RetrievedSource {
  bytes: Buffer;
  mediaType: string;
  title: string;
  canonicalSource: string;
  author?: string;
  publisher?: string;
  publishedAt?: string;
  metadata: Record<string, unknown>;
}

type Fetcher = (url: string) => Promise<Response>;
type TranscriptFetcher = (url: string) => Promise<Array<{ offset: number; duration: number; text: string; lang?: string }>>;

export interface SourceAdapter {
  readonly type: SourceType;
  supports(input: string): boolean;
  retrieve(input: string): Promise<RetrievedSource>;
}

function detectType(input: string): SourceType {
  if (/youtu\.be|youtube\.com/i.test(input)) return "youtube";
  if (/arxiv\.org/i.test(input)) return "arxiv";
  if (/^https?:/i.test(input)) return input.toLowerCase().endsWith(".pdf") ? "pdf" : "webpage";
  return extname(input).toLowerCase() === ".pdf" ? "pdf" : "file";
}

async function fetchChecked(url: string): Promise<Response> {
  const response = await fetch(url, { redirect: "follow", headers: { "user-agent": "climbhill/0.2" } });
  if (!response.ok) throw new Error(`retrieval failed (${response.status}) for ${url}`);
  return response;
}

export class FileAdapter implements SourceAdapter {
  readonly type: SourceType = "file";
  supports(input: string) { return !/^https?:/i.test(input); }
  async retrieve(input: string): Promise<RetrievedSource> {
    const path = resolve(input);
    await access(path);
    return { bytes: await readFile(path), mediaType: "text/plain", title: basename(path), canonicalSource: path, metadata: {} };
  }
}

export class PdfAdapter implements SourceAdapter {
  readonly type: SourceType = "pdf";
  constructor(private readonly fetcher: Fetcher = fetchChecked) {}
  supports(input: string) { return input.toLowerCase().endsWith(".pdf"); }
  async retrieve(input: string): Promise<RetrievedSource> {
    if (!/^https?:/i.test(input)) {
      const path = resolve(input);
      return { bytes: await readFile(path), mediaType: "application/pdf", title: basename(path), canonicalSource: path, metadata: { locator: "page" } };
    }
    const response = await this.fetcher(input);
    return { bytes: Buffer.from(await response.arrayBuffer()), mediaType: response.headers.get("content-type") || "application/pdf", title: basename(new URL(response.url).pathname) || "document.pdf", canonicalSource: response.url, metadata: { locator: "page" } };
  }
}

export class WebpageAdapter implements SourceAdapter {
  readonly type: SourceType = "webpage";
  constructor(private readonly fetcher: Fetcher = fetchChecked) {}
  supports(input: string) { return /^https?:/i.test(input); }
  async retrieve(input: string): Promise<RetrievedSource> {
    const response = await this.fetcher(input);
    const bytes = Buffer.from(await response.arrayBuffer());
    const text = bytes.toString("utf8");
    const title = text.match(/<title[^>]*>([^<]+)<\/title>/i)?.[1]?.trim() || new URL(response.url).hostname;
    return { bytes, mediaType: response.headers.get("content-type") || "text/html", title, canonicalSource: response.url, metadata: { status: response.status } };
  }
}

export class YouTubeAdapter implements SourceAdapter {
  readonly type: SourceType = "youtube";
  constructor(
    private readonly fetcher: Fetcher = fetchChecked,
    private readonly transcriptFetcher: TranscriptFetcher = (url) => fetchTranscript(url),
  ) {}
  supports(input: string) { return /youtu\.be|youtube\.com/i.test(input); }
  async retrieve(input: string): Promise<RetrievedSource> {
    const endpoint = `https://www.youtube.com/oembed?url=${encodeURIComponent(input)}&format=json`;
    const metadata = await (await this.fetcher(endpoint)).json() as { title: string; author_name: string; provider_name: string };
    const transcript = await this.transcriptFetcher(input);
    const artifact = { video: { url: input, title: metadata.title, author: metadata.author_name, publisher: metadata.provider_name }, transcript: transcript.map((segment) => ({ timestampMs: segment.offset, durationMs: segment.duration, text: segment.text, lang: segment.lang })) };
    return { bytes: Buffer.from(`${JSON.stringify(artifact, null, 2)}\n`), mediaType: "application/json", title: metadata.title, canonicalSource: input, author: metadata.author_name, publisher: metadata.provider_name, metadata: { locator: "timestamp", transcriptSegments: transcript.length } };
  }
}

export class ArxivAdapter implements SourceAdapter {
  readonly type: SourceType = "arxiv";
  constructor(private readonly fetcher: Fetcher = fetchChecked) {}
  supports(input: string) { return /arxiv\.org/i.test(input); }
  async retrieve(input: string): Promise<RetrievedSource> {
    const id = input.match(/(?:abs|pdf)\/([^?#]+?)(?:\.pdf)?$/)?.[1];
    if (!id) throw new Error(`could not parse arXiv identifier from ${input}`);
    const api = await (await this.fetcher(`https://export.arxiv.org/api/query?id_list=${encodeURIComponent(id)}`)).text();
    const versionedId = api.match(/<entry>[\s\S]*?<id>https?:\/\/arxiv\.org\/abs\/([^<]+)<\/id>/)?.[1] || id;
    const pdfUrl = `https://arxiv.org/pdf/${versionedId}.pdf`;
    const pdf = await this.fetcher(pdfUrl);
    const title = api.match(/<entry>[\s\S]*?<title>([\s\S]*?)<\/title>/)?.[1]?.replace(/\s+/g, " ").trim() || id;
    const author = [...api.matchAll(/<author>\s*<name>(.*?)<\/name>/g)].map((match) => match[1]).join(", ");
    const publishedAt = api.match(/<published>(.*?)<\/published>/)?.[1];
    return { bytes: Buffer.from(await pdf.arrayBuffer()), mediaType: "application/pdf", title, canonicalSource: `https://arxiv.org/abs/${versionedId}`, author, publisher: "arXiv", publishedAt, metadata: { arxivId: versionedId, requestedId: id, apiMetadata: api, originalPdf: pdfUrl, locator: "page" } };
  }
}

export const sourceAdapters: SourceAdapter[] = [new YouTubeAdapter(), new ArxivAdapter(), new PdfAdapter(), new WebpageAdapter(), new FileAdapter()];

export async function addSource(root: string, input: string, explicitType?: SourceType, adapters: SourceAdapter[] = sourceAdapters): Promise<{ resource: ResourceVersion; duplicate: boolean }> {
  const type = explicitType || detectType(input);
  const adapter = adapters.find((candidate) => candidate.type === type && candidate.supports(input));
  if (!adapter) throw new Error(`no ${type} adapter accepts ${input}`);
  const retrieved = await adapter.retrieve(input);
  const contentHash = hash(retrieved.bytes);
  const logicalId = `resource-${hash(`${type}:${retrieved.canonicalSource}`).slice(0, 16)}`;
  const resourceDirectory = join(root, "research", "okf", "resources");
  const existing: ResourceVersion[] = [];
  for (const name of (await readdir(resourceDirectory)).filter((value) => value.startsWith(`${logicalId}-v`) && value.endsWith(".md"))) {
    const parsed = parseFrontmatter<ResourceVersion>(await readFile(join(resourceDirectory, name), "utf8"));
    existing.push(parsed.data);
  }
  const duplicate = existing.find((version) => version.contentHash === contentHash);
  if (duplicate) return { resource: duplicate, duplicate: true };
  const version = Math.max(0, ...existing.map((value) => value.version)) + 1;
  const id = `${logicalId}-v${version}`;
  const extension = type === "pdf" || type === "arxiv" ? ".pdf" : type === "youtube" ? ".json" : type === "webpage" ? ".html" : extname(input) || ".txt";
  const rawPath = `research/raw/${contentHash}${extension}`;
  await atomicWrite(join(root, rawPath), retrieved.bytes);
  const resource: ResourceVersion = {
    id, logicalId, version, type, source: retrieved.canonicalSource, title: retrieved.title,
    ...(retrieved.author ? { author: retrieved.author } : {}), ...(retrieved.publisher ? { publisher: retrieved.publisher } : {}),
    ...(retrieved.publishedAt ? { publishedAt: retrieved.publishedAt } : {}), retrievedAt: now(), contentHash, rawPath,
    mediaType: retrieved.mediaType, metadata: retrieved.metadata, derivationStatus: "pending",
  };
  await atomicWrite(join(resourceDirectory, `${id}.md`), frontmatter(resource as unknown as Record<string, unknown>, `# ${resource.title}\n\nSource: ${resource.source}\n`));
  return { resource, duplicate: false };
}

export async function extractText(root: string, resource: ResourceVersion): Promise<string> {
  const raw = join(root, resource.rawPath);
  if (resource.mediaType !== "application/pdf") return readFile(raw, "utf8");
  try {
    const { stdout } = await execFileAsync("pdftotext", ["-layout", raw, "-"]);
    return stdout.split("\f").map((page, index) => `--- PAGE ${index + 1} ---\n${page.trim()}`).join("\n\n");
  } catch {
    throw new Error("PDF derivation requires the 'pdftotext' executable; ingestion was preserved");
  }
}

export async function updateResource(root: string, resource: ResourceVersion): Promise<void> {
  await writeConcept(
    join(root, "research", "okf", "resources", `${resource.id}.md`),
    resource as unknown as Record<string, unknown>,
    `# ${resource.title}\n\nSource: ${resource.source}\n`,
  );
}
