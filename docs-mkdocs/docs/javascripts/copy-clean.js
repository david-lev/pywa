/* Copy only the code of ">>>"/"..." (pycon) blocks, without prompts or output lines. */
function pwCleanPycon(block) {
  const code = block.querySelector("code");
  if (!code || !code.querySelector(".gp")) return null;
  return code.textContent.split("\n")
    .filter((l) => l.startsWith(">>> ") || l.startsWith("... ") || l === "..." || l === ">>>")
    .map((l) => l.slice(4))
    .join("\n");
}
document.addEventListener("click", (ev) => {
  const btn = ev.target.closest && ev.target.closest('button[data-md-type="copy"]');
  if (!btn) return;
  const pre = document.querySelector(btn.getAttribute("data-clipboard-target").replace(/ > code$/, ""));
  const text = pre && pwCleanPycon(pre);
  if (text === null || text === undefined) return;
  btn.setAttribute("data-clipboard-text", text);
}, true);
