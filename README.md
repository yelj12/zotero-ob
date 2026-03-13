# 本地 PDF 导入 Zotero（本地 API）

这个仓库提供一个脚本：`import_pdf_to_zotero.py`，用于把本地 PDF 文件通过 Zotero 本地接口导入到文库。

默认接口地址：`http://localhost:23119/api`

## 用法

```bash
python3 import_pdf_to_zotero.py /path/to/file.pdf
```

可选参数：

- `--api-base`：API 基础地址（默认 `http://localhost:23119/api`）
- `--api-key`：如果你启用了写入鉴权，可传入 API Key
- `--library-type`：`users` 或 `groups`（默认 `users`）
- `--library-id`：文库 ID（默认 `0`）

示例：

```bash
python3 import_pdf_to_zotero.py ~/Downloads/paper.pdf \
  --api-base http://localhost:23119/api \
  --library-type users \
  --library-id 0
```

## 导入前检查

1. Zotero 已启动。
2. 本地 API 可访问：

```bash
curl http://localhost:23119/api/
```

3. PDF 文件路径正确。

## 返回说明

- 成功：输出 `Import succeeded` 以及接口返回内容。
- 失败：输出 HTTP 状态码和错误详情。
