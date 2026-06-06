export function formatNOK(n: number): string {
  // nb-NO grouping separator is U+00A0 (non-breaking space) or U+202F (narrow no-break space)
  // depending on Node/ICU version. Normalize both to regular space so tests pass deterministically.
  return n.toLocaleString('nb-NO').replace(/[  ]/g, ' ') + ',—';
}
