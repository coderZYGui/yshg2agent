type ClipboardItem = Pick<DataTransferItem, "kind" | "getAsFile">;

export function getPastedFiles(items: Iterable<ClipboardItem>): File[] {
  const files: File[] = [];
  for (const item of items) {
    if (item.kind !== "file") continue;
    const file = item.getAsFile();
    if (file) files.push(file);
  }
  return files;
}
