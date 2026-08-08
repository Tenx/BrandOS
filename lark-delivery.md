# Feishu / Lark — Client Delivery Workflow

Used when delivering Brand OS strategy reports, PDFs, and documents to clients via Feishu Drive.

## Folder structure convention

```
Brand OS/                          ← EO44fUp19lmA1IdKIZ6cggEonwb
└── 客户交付/                       ← create once, reuse for all clients
    └── <BrandName> · <产品名>/     ← one folder per client engagement
        ├── <Brand>-hound.pdf
        ├── <Brand>-bee.pdf
        └── <Brand> · 客户交付说明  ← Feishu docx with links + summary
```

## Create folder

```bash
# Create 客户交付 (if not exists)
lark-cli drive +create-folder --name "客户交付" --folder-token EO44fUp19lmA1IdKIZ6cggEonwb

# Create brand subfolder
lark-cli drive +create-folder --name "<Brand> · <产品名>" --folder-token <客户交付_token>
```

## Upload files

`+upload --file` only accepts **relative paths within cwd**. Always `cd` to the file directory first:

```bash
cd /path/to/files
lark-cli drive +upload --file ./report.pdf --folder-token <folder_token>
```

For files in a different directory, copy to a temp location first or use the cwd trick.

## Create delivery note doc

`docs +create` v2 uses `--parent-token` (not `--folder-token`, which is removed).
Use stdin (`--content -`) for multiline markdown content:

```bash
lark-cli docs +create \
  --title "<Brand> · 客户交付说明" \
  --doc-format markdown \
  --content - \
  --parent-token <folder_token> \
  < /path/to/delivery-note.md
```

## Set public link access

`permission.public patch` does **NOT support `--type folder`** — folder is not in the enum.
Set permissions file-by-file only.

For each file (PDF) and docx:
```bash
lark-cli drive permission.public patch \
  --token <file_token> \
  --type file   # or: docx / sheet / bitable / slides
  --data '{"external_access":true,"link_share_entity":"anyone_readable"}' \
  --yes
```

**Both fields required together:**
- `external_access: true` — allows sharing outside the org (prerequisite)
- `link_share_entity: "anyone_readable"` — internet link readable without login

Without `external_access: true`, `anyone_readable` has no effect (falls back to tenant-only).

Parallel execution for multiple files:
```bash
DATA='{"external_access":true,"link_share_entity":"anyone_readable"}'
lark-cli drive permission.public patch --token <token1> --type file --data "$DATA" --yes &
lark-cli drive permission.public patch --token <token2> --type file --data "$DATA" --yes &
lark-cli drive permission.public patch --token <token3> --type docx --data "$DATA" --yes &
wait
```

## Verify permissions

```bash
lark-cli drive +permission-get-setting --token <token> --type file \
  | grep '"link_share_entity"'
# Expected: "link_share_entity": "anyone_readable"
```

## Public URLs

File URLs follow the pattern:
- PDF / file: `https://my.feishu.cn/file/<file_token>`
- Docx: `https://my.feishu.cn/docx/<document_id>`
- Folder: `https://my.feishu.cn/drive/folder/<folder_token>` (not publicly accessible)
