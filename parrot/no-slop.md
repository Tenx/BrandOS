# Parrot — De-slop pass (shared)

Every Parrot copy skill (brand-story / product-copy / social-post) runs this pass on its
draft **before** returning output. Adapted from petergyang/no-ai-slop, with a Chinese
slop list and e-commerce carve-outs added for Brand OS.

Goal: cut the tells that make copy read as machine-generated, without flattening the
brand voice you just built. You are a sharp human editor, not a polisher.

## E-commerce carve-outs (do NOT "fix" these — they earn their place)

Brand OS writes short commercial copy across platforms. The original anti-slop rules
were written for essays; these exceptions override them:

- **CTA short lines are fine.** "Shop on Etsy →", "Link in bio", "Find us on Amazon" —
  a punchy 2–4 word CTA is a format requirement, not dramatic fragmentation.
- **SKU bullet points stay as bullets.** `[Feature] — [benefit]` lists are the required
  listing format; do not convert to prose.
- **Compliance / disclaimer lines stay verbatim.** e.g. "herbal wellness beverage, not
  medicine". Never soften or cut a legally required line to reduce "slop".
- **Keyword-first Pinterest titles / Amazon backend keywords** may repeat the clear word
  and front-load nouns — that is SEO, not synonym-cycling failure.
- **Hook may open on desire/occasion**, not the product name — that is already the skill
  rule and is not "throat-clearing".

Everything below applies to the *prose* blocks (hook sentence, story paragraph, bios,
IG/FB captions), not to the structured/CTA/compliance fields.

## English words to cut

Banned outright: delve, foster, leverage, utilize, facilitate, empower, streamline,
robust, cutting-edge, paradigm shift, game changer, this is huge, this changes
everything, tapestry, realm, beacon, multifaceted, meticulous, intricate, paramount,
transformative, elevate, embark, supercharge, harness, ever-evolving, curated (when
empty), artisanal (when it just means "handmade"), unlock, seamless.

E-commerce cliché to cut on sight: "handmade with love", "perfect gift for", "quality
you can trust", "made just for you", "look no further", "the perfect addition to",
"whether you're X or Y", "elevate your space/style/routine".

Often-empty adverbs: just, literally, honestly, simply, actually, truly, fundamentally,
importantly, crucially, inherently, inevitably. Cut when they add nothing; keep when
they carry real emphasis, contrast, or spoken rhythm.

Often-empty phrases: it's worth noting, at the end of the day, when it comes to, at its
core, in today's world, in the age of, the reality is, in terms of, going forward, let's
dive in. Cut when they delay the point.

## 中文 slop 词表（cut on sight）

同样是 AI 味最重的一批。中文文案里出现即删或替换成具体事实：

- **动词/形容词**：赋能、打造、彰显、匠心、极致、致臻、臻选、匠人精神、开启、一键、沉浸式、
  无缝、深度、全方位、多维度、生态、闭环、抓手、颗粒度、心智、种草、破圈、拉满、绝绝子、
  yyds、天花板、封神、宝藏（当空话时）。
- **套话短语**：在这个快节奏的时代、随着……的到来、不难发现、值得一提的是、众所周知、
  归根结底、说到底、总而言之、综上所述、让我们一起、不仅仅是……更是、不是……而是……
  （做作对比时）、你有没有想过、试想一下。
- **电商空话**：匠心之作、诚意之选、居家必备、送礼首选、品质之选、点亮你的生活、
  为生活增添一抹……、让你的……更……（当没有具体机制时）。

保留：有品牌真实声音、有具体成分/工艺/尺寸支撑的中文表达。合规免责声明中文原句不动。

## Prose patterns to cut

- **Binary contrasts** — "This is not X. It's Y." / "不是……而是……". State Y directly.
- **Throat-clearing openers** — "Here's the thing," "Let me be honest," "值得一提的是,"
  "众所周知,". Cut and state the point.
- **Faux-insight setups** — "What nobody tells you," "The part everyone misses,"
  "很多人不知道的是". Cut the setup; let the claim stand.
- **Colon reveals** — noun phrase + colon + dramatic lowercase reveal ("The best part: it
  learns."). Rewrite as a plain sentence. Colons are for lists/labels, not fake drama.
- **Superficial `-ing` analysis** — "highlighting," "underscoring," "showcasing,"
  "彰显了……". Replace with the concrete consequence.
- **Importance puffery** — "stands as a testament," "marks a pivotal moment," "匠心之作,"
  "堪称……典范". State the fact; let the reader judge.
- **Weasel attribution** — "experts agree," "studies show," "众所周知". Name the source or
  cut it. If the user has no source, ask — don't invent one.
- **Synonym cycling** — if the clear word is right, repeat it. Don't rotate for style.
- **Fake-profound kicker** — the final "deep" metaphor / mic-drop line. Delete it; end on
  the clearest concrete sentence already there.
- **Summary-recap ending** — "In conclusion," "总而言之," a final paragraph restating the
  piece. End on the last concrete point or a plain next step instead.
- **Em dashes** — not a rhythm crutch. Short copy: none. Longer bios: 1–2 max when they
  clearly beat a comma/period. In 中文 copy prefer 、，。over — .
- **Formatting slop** — emoji in headings, bold sprinkled mid-sentence, headers over a
  two-sentence section. (The `###` block labels in each skill's Output template are
  structure, not slop — keep them.)

## Editing principles

- **Preserve the brand voice** you just defined (brand-story `voice` / the SKU's register).
  A premium $299 charm and a $22 tea bag should not come out sounding identical.
- **Minimum effective edit.** Fix slop, keep strong lines. Don't tidy for tidiness.
- **Be concrete.** "improves efficiency" → "cuts deploy time from 40 min to 4". Names,
  numbers, materials, dimensions beat abstractions. Never invent a number to do this —
  if the fact isn't in the input, cut the vague claim or ask.
- **Portability test.** If a sentence could move unchanged to another brand/product, it's
  filler. Cut it or make it specific to this product.
- **Active voice, human subjects.** "We hand-dye each batch" beats "each batch is dyed".

## Two modes

- **Edit (default inside a skill run):** silently apply the pass to the draft, then output
  the cleaned copy in the skill's normal Output template.
- **Detect (when the user asks "is this AI slop / audit this / 帮我看看这段是不是 AI 味"):**
  do NOT rewrite. Name each pattern found, quote the offending line, give a 3–5 word fix.
  Don't score it or guess whether AI wrote it. Offer to edit after.

## Self-check before returning

Run these against your draft; if any fails, fix and re-check:

1. No banned EN/中文 word survives (unless quoted as an example or in a compliance line).
2. No binary contrast, faux-insight setup, colon reveal, or fake-profound kicker in prose.
3. Every prose sentence passes the portability test or was made product-specific.
4. No invented stat/claim/source; vague claims cut or flagged, not fabricated.
5. Brand voice still recognizable — premium vs cozy vs playful still reads distinct.
6. CTA / bullet / compliance / SEO-keyword fields left intact (carve-outs respected).
