import { css } from "remix/ui";

const font = "Inter, ui-sans-serif, system-ui, sans-serif";
const mono = "'SFMono-Regular', Consolas, 'Liberation Mono', monospace";

export function Home() {
  return () => (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="description" content="Local-first recursive research and repository improvement." />
        <title>ClimbHill</title>
      </head>
      <body mix={css({ margin: 0, color: "#181818", background: "#f5f4ef", fontFamily: font, letterSpacing: 0 })}>
        <header mix={css({ height: "64px", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 clamp(20px, 5vw, 72px)", background: "#f5f4ef", borderBottom: "1px solid #181818", position: "relative", zIndex: 2 })}>
          <strong mix={css({ fontSize: "18px" })}>ClimbHill</strong>
          <nav aria-label="Primary" mix={css({ display: "flex", gap: "24px", fontSize: "14px" })}>
            <a href="https://github.com/closedloop-technologies/climbhill" mix={css({ color: "inherit" })}>GitHub</a>
            <a href="#install" mix={css({ color: "inherit" })}>Install</a>
          </nav>
        </header>
        <main>
          <section mix={css({ minHeight: "calc(100svh - 112px)", position: "relative", display: "grid", alignItems: "end", overflow: "hidden", background: "#101414" })}>
            <img src="/assets/hero-research-harness.png" alt="ClimbHill research workflow interface" mix={css({ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", opacity: 0.62 })} />
            <div mix={css({ position: "absolute", inset: 0, background: "linear-gradient(0deg, rgba(16,20,20,0.94) 0%, rgba(16,20,20,0.2) 72%)" })} />
            <div mix={css({ position: "relative", color: "#ffffff", padding: "64px clamp(20px, 7vw, 104px) 72px", maxWidth: "900px" })}>
              <h1 mix={css({ margin: 0, fontSize: "clamp(52px, 9vw, 112px)", lineHeight: 0.92, fontWeight: 750, letterSpacing: 0 })}>ClimbHill</h1>
              <p mix={css({ margin: "28px 0 0", maxWidth: "680px", fontSize: "clamp(18px, 2.2vw, 28px)", lineHeight: 1.35 })}>Build repository workflows that research, attempt, evaluate, and remember, with every decision grounded in local evidence.</p>
            </div>
          </section>
          <section id="install" mix={css({ display: "grid", gridTemplateColumns: "minmax(0, 1.1fr) minmax(280px, 0.9fr)", gap: "clamp(32px, 8vw, 120px)", padding: "clamp(64px, 10vw, 144px) clamp(20px, 7vw, 104px)", background: "#d9ff43", borderTop: "1px solid #181818", '@media (max-width: 760px)': { gridTemplateColumns: "1fr" } })}>
            <div>
              <p mix={css({ margin: "0 0 14px", fontFamily: mono, fontSize: "13px", textTransform: "uppercase" })}>Local first. Git native.</p>
              <h2 mix={css({ margin: 0, fontSize: "clamp(34px, 5vw, 64px)", lineHeight: 1.02, letterSpacing: 0 })}>Evidence compounds. Failures remain useful.</h2>
            </div>
            <div mix={css({ alignSelf: "end" })}>
              <p mix={css({ fontSize: "18px", lineHeight: 1.55, margin: "0 0 24px" })}>Research is inspectable Markdown. Attempts are bounded run records. Promotion stays human-approved.</p>
              <pre mix={css({ margin: 0, padding: "18px 20px", overflowX: "auto", background: "#181818", color: "#ffffff", borderRadius: "4px", fontFamily: mono, fontSize: "14px" })}><code>npm install -g climbhill</code></pre>
            </div>
          </section>
          <section mix={css({ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", borderTop: "1px solid #181818", borderBottom: "1px solid #181818", '@media (max-width: 760px)': { gridTemplateColumns: "1fr" } })}>
            {[
              ["01", "Ingest", "Preserve source bytes, hashes, versions, and exact evidence locators."],
              ["02", "Derive", "Use typed BAML functions to produce source-local observations."],
              ["03", "Reconcile", "Build an explicit graph without hiding conflicts or uncertain identity."],
            ].map(([number, title, copy], index) => (
              <article key={number} mix={css({ padding: "48px clamp(20px, 4vw, 56px)", borderRight: index < 2 ? "1px solid #181818" : 0, '@media (max-width: 760px)': { borderRight: 0, borderBottom: index < 2 ? "1px solid #181818" : 0 } })}>
                <span mix={css({ fontFamily: mono, color: "#c13b2a", fontWeight: 700 })}>{number}</span>
                <h3 mix={css({ margin: "24px 0 12px", fontSize: "24px", letterSpacing: 0 })}>{title}</h3>
                <p mix={css({ margin: 0, lineHeight: 1.6 })}>{copy}</p>
              </article>
            ))}
          </section>
        </main>
        <footer mix={css({ display: "flex", justifyContent: "space-between", gap: "24px", padding: "32px clamp(20px, 5vw, 72px)", background: "#f5f4ef", fontSize: "13px" })}>
          <span>ClimbHill.ai</span><span>Local-first agentic workflows</span>
        </footer>
      </body>
    </html>
  );
}
