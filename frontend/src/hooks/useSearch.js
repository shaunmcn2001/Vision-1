/**
 * Fetch parcels from the back‑end given an array of lot/plan strings.
 *
 * The back‑end automatically determines which service (QLD or NSW) to
 * query based on the format of the input.  The response includes a
 * `features` array containing GeoJSON feature objects.
 */
export async function fetchParcels(inputs) {
  const base = import.meta.env.VITE_API_BASE || '';
  const r = await fetch(`${base}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ inputs }),
  });
  if (!r.ok) {
    throw new Error(`Server error ${r.status}`);
  }
  return r.json();
}