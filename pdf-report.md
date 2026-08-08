# PDF Report Generation — Puppeteer Headless Chrome

Used when outputting Brand OS strategy reports (Hound + Bee combined, or per-module).

## Tool choice

**Puppeteer + system Chrome** is the most reliable option for HTML→PDF with custom fonts,
background colors, and precise layout. Do NOT use:
- `wkhtmltopdf` — not installed, poor CSS support
- `weasyprint` — not installed
- Chrome `⌘P` → Save as PDF — works but requires user interaction

Puppeteer is installed globally — find path with `npm root -g`.

## Puppeteer script template

```javascript
const puppeteer = require(require('child_process').execSync('npm root -g').toString().trim() + '/puppeteer');
const { setTimeout: sleep } = require('timers/promises');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 794, height: 1123, deviceScaleFactor: 2 });

  await page.goto('file:///absolute/path/to/report.html', {
    waitUntil: 'networkidle0',
    timeout: 30000
  });
  await sleep(3000); // wait for Google Fonts to fully load

  await page.pdf({
    path: '/absolute/path/to/output.pdf',
    format: 'A4',
    printBackground: true,
    margin: { top: 0, right: 0, bottom: 0, left: 0 },
    preferCSSPageSize: true,
  });

  await browser.close();
})();
```

Run with: `node /tmp/render.js`

**API notes:**
- `page.waitForTimeout()` removed in Puppeteer v25+; use `timers/promises` sleep instead
- `require('puppeteer')` fails from `/tmp` — always use the absolute global path

## HTML page structure — avoid blank pages

**Root cause of blank pages**: `min-height: 297mm` + `page-break-after: always` on the same
element causes Puppeteer to insert a blank page after every content page.

**Correct CSS pattern:**
```css
.page {
  width: 210mm;
  /* NO min-height here */
  margin: 0 auto;
  position: relative;
  overflow: hidden;
  background: var(--bg);
  break-after: page;          /* use break-after, NOT page-break-after */
}

/* Cover page is full A4 height — use fixed height, not min-height */
.cover {
  height: 297mm;              /* fixed, not min-height */
  display: flex;
  flex-direction: column;
}

@media print {
  body { background: var(--bg); }
  .page { break-after: page; margin: 0; }
  @page { margin: 0; size: A4; }
}
```

**Rule**: only the cover gets `height: 297mm`. All other pages use `height: auto` (no declaration)
and let content fill naturally. `break-after: page` handles the page split.

## Splitting one HTML into multiple PDFs

To generate separate PDFs from one source file, use Python to split by section markers:

```python
with open('report.html') as f:
    content = f.read()

split_marker = '<!-- PAGE: BEE -->'  # put a comment at the split point in HTML
head = content[:content.find('<body>') + len('<body>')]
hound_body = content[content.find('<body>') + len('<body>'): content.find(split_marker)]
bee_body    = content[content.find(split_marker): content.rfind('</body>')]

with open('hound.html', 'w') as f:
    f.write(head + hound_body + '</body></html>')

with open('bee.html', 'w') as f:
    f.write(head + bee_body + '</body></html>')
```

Then render each HTML separately with the Puppeteer script above.

## Google Fonts in offline / file:// context

Google Fonts load from CDN — they work in `file://` pages as long as the machine has internet.
`waitUntil: 'networkidle0'` + `sleep(3000)` is sufficient to wait for font rendering.
If fonts must work offline, download and embed as base64 in `<style>` instead.

---

# Hero Photo Generation — Replicate gpt-image-2

Used for all Brand OS product hero image generation (non-fashion/non-apparel products).
For jewellery/craft/accessory products, use this directly instead of `ai-hero-photo` skill.

## Version hash

```
225c978a7f938acc350564c4548ddc2476bfb33364bec6b5422227f55ce56bd3
```

Always fetch latest at runtime:
```bash
TOKEN=<replicate_token>
curl -s -H "Authorization: Bearer $TOKEN" \
  https://api.replicate.com/v1/models/openai/gpt-image-2 \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['latest_version']['id'])"
```

## API call pattern

Use `version` field (NOT `model`). Pass `image` as a Replicate Files API URL (not base64):

```python
# Step 1: upload source image to Replicate Files API (avoids timeout on large PNGs)
r = requests.post(
    "https://api.replicate.com/v1/files",
    headers={"Authorization": f"Bearer {token}"},
    files={"content": (filename, open(path,"rb"), "image/png")},
    timeout=120,
)
file_url = r.json()["urls"]["get"]

# Step 2: create prediction
payload = {
    "version": "<version_hash>",
    "input": {
        "prompt": "...",
        "image": file_url,   # URL from Files API, NOT base64
        "quality": "high",
        "size": "1024x1024",
        "output_format": "png",
    }
}
r = requests.post("https://api.replicate.com/v1/predictions",
    json=payload, headers={"Authorization": f"Bearer {token}"}, timeout=120)

# Step 3: poll
while result["status"] not in ("succeeded","failed","canceled"):
    time.sleep(8)
    result = requests.get(result["urls"]["get"], ...).json()

# Step 4: download
img_bytes = requests.get(result["output"][0], timeout=60).content
```

**Key lessons:**
- `model` field → 422 error; use `version` field instead
- base64 image in payload → `RemoteDisconnected` / write timeout on files >4MB; always use Files API URL
- `urllib` hangs on large payloads; use `requests` library
- `Prefer: wait` header unreliable; always poll manually

## 4-shot template for product charms / accessories

```
Shot 1 — Flat lay: warm parchment background, soft side light, white felt border visible, centered
Shot 2 — Bag hang lifestyle: dark tote bag, cafe/street bokeh, charm in focus, editorial mood
Shot 3 — Dramatic dark: black bg, single spotlight, silk fabric, smoke/incense prop, cinematic
Shot 4 — Variant spread: 5 items in arc/row, each different color, shows blind box variety
```

## WooCommerce image attachment

```python
# Import to media + attach to product (must cd into WP dir first)
subprocess.run([
    "php", "-d", "memory_limit=512M", "-d", "error_reporting=E_ALL&~E_DEPRECATED",
    "/opt/homebrew/bin/wp",
    "media", "import", "/abs/path/to/image.png",
    "--title=product-image-name",
    f"--post_id={product_id}",
    "--porcelain",
], cwd="/path/to/wordpress", ...)

# Set as product images (use subprocess, NOT shell — bracket quoting breaks in zsh)
subprocess.run([..., "wc", "product", "update", str(product_id),
    "--user=admin",
    '--images=[{"id":17},{"id":18},{"id":19},{"id":20}]',
])
```
