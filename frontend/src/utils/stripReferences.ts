export function stripReferenceTags(content: string) {
  return content.replace(/<ref>.*?<\/ref>/g, "");
}
