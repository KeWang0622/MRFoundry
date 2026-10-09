# Programmatic access to literature & data: APIs, keys, and MCP servers

[MRFoundry](https://github.com/KeWang0622/MRFoundry) · [Reference index](https://github.com/KeWang0622/MRFoundry/blob/main/REFERENCES.md)

Use this when the user wants to *find, fetch, or monitor* MR papers/datasets
programmatically — or asks which resources need an API key or whether there's
an MCP server for it. This lets the skill actually retrieve current information
instead of relying on frozen knowledge.

## Scholarly-literature APIs (most are free)

| Source | What it's good for | Auth / key |
|---|---|---|
| **arXiv API** (https://info.arxiv.org/help/api/) | Preprints (physics.med-ph, eess.IV, cs.CV) — where MR-recon methods appear first | None; be polite with rate limits |
| **PubMed / NCBI E-utilities** (https://www.ncbi.nlm.nih.gov/books/NBK25501/) | Clinical + MRM/JMRI indexed literature | Works without a key; a free **NCBI API key** raises rate limits (3→10 req/s) |
| **Semantic Scholar Graph API** (https://api.semanticscholar.org/) | Citations, references, embeddings, TLDರ summaries | Works unauthenticated at low rate; free **S2 API key** for higher limits |
| **OpenAlex** (https://docs.openalex.org/) | Fully open metadata graph (works, authors, venues); great for surveys | None; add your email as `mailto=` for the polite pool |
| **Crossref REST API** (https://api.crossref.org/) | DOI metadata, resolving citations | None; add `mailto=` for the polite pool |
| **Europe PMC** (https://europepmc.org/RestfulWebService) | Full-text where open-access; life-sciences | None |

Practical guidance:
- For "find the latest on X recon," query **arXiv** (recency) + **Semantic
  Scholar/OpenAlex** (citation graph) together, then dedupe by DOI/title.
- Respect rate limits and terms; identify yourself (email/`mailto`) where the
  API asks. Do not scrape paywalled full text — fetch metadata and open-access
  PDFs only.
- If a key is needed, the user supplies their own. Read it from an environment
  variable (e.g., `S2_API_KEY`, `NCBI_API_KEY`) — **never hard-code a key into
  a script or commit it.** Treat any pasted key as a secret: use it transiently
  and remind the user to rotate it if it was exposed.

## MCP servers for paper search

If the session has (or the user wants to add) an MCP server, these expose the
APIs above as tools so you can search/fetch papers directly. Community options
(verify the current repo/URL and vet before installing — MCP servers run code):

- **paper-search-mcp** — arXiv/PubMed/bioRxiv/etc. search + download:
  https://github.com/openags/paper-search-mcp (uses `S2_API_KEY` if provided).
- **paper-mcp** (MCPServings) — arXiv/Semantic Scholar/OpenAlex + PubMed/Europe
  PMC + LaTeX/PDF tools: https://github.com/mcpservings/paper-mcp
- **academic-mcp** — multi-source search/download:
  https://github.com/LinXueyuanStdio/academic-mcp

When one of these is connected, prefer it over ad-hoc web fetching for
literature — it returns structured metadata (DOIs, abstracts, citation counts)
you can cite cleanly.

## Dataset access (auth summary)

- **fastMRI** — requires a signed **data-use agreement / application** at
  https://fastmri.med.nyu.edu before download; do not circumvent it.
- **mridata.org** — open download, but **per-dataset license terms** apply;
  surface the terms for the specific dataset.
- **OCMR** — open (https://ocmr.info).
- If the user needs credentials/keys for any of these, they provide their own;
  handle as secrets (env vars, transient use, never committed).

## When Claude Code has WebSearch/WebFetch but no MCP

You can still do literature lookups with the built-in web tools: search for the
topic + "arXiv"/"Magnetic Resonance in Medicine," then fetch the abstract/PDF
landing page. Always cite with a resolvable link (DOI or arXiv id) so the user
can reach it through their own institutional access.
