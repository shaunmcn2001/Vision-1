import React, {useState, useContext} from 'react';
import {SearchContext} from './SearchContext.js';
import {fetchParcels} from './hooks/useSearch.js';

/**
 * QueryPanel is rendered inside the kepler.gl side panel when injected via
 * CustomSidePanelFactory.  It allows the user to enter a list of lot/plan
 * identifiers, perform a search and adjust styling and download options.
 *
 * All state and actions are consumed from SearchContext provided by the
 * App component.
 */
export default function QueryPanel() {
  const {
    onResults,
    features = [],
    selected = {},
    toggle,
    download,
    style = {},
    setStyle,
  } = useContext(SearchContext);

  const [bulk, setBulk] = useState('');
  const [folderName, setFolderName] = useState('Parcels');
  const [fileName, setFileName] = useState('parcels.kml');
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    const lines = bulk
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);
    if (!lines.length) return;
    setLoading(true);
    try {
      const data = await fetchParcels(lines);
      onResults && onResults(data.features || []);
    } catch (err) {
      // eslint-disable-next-line no-alert
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const updateStyle = (p) => {
    setStyle && setStyle({ ...style, ...p });
  };
  const downloadWithMeta = (t) => {
    const fname = t === 'kml' ? fileName : fileName.replace(/\.kml$/i, '.zip');
    download && download(t, folderName, fname);
  };

  return (
    <div className="p-3 text-sm overflow-y-auto" style={{maxHeight: '100%'}}>
      <h3 className="font-semibold mb-2">Search Parcels</h3>
      <textarea
        className="input-base w-full h-28 mb-2"
        value={bulk}
        onChange={(e) => setBulk(e.target.value)}
        placeholder="QLD 3RP123456\nNSW 4/DP765432"
      />
      <button className="btn-primary w-full mb-2" onClick={handleSearch} disabled={loading}>
        {loading ? 'Searching…' : 'Search'}
      </button>
      {features.length > 0 && (
        <>
          <hr className="my-3 border-gray-700" />
          <h4 className="font-semibold mb-1">Export</h4>
          <label className="block mb-1">
            Folder name
            <input
              className="input-base w-full mt-1"
              value={folderName}
              onChange={(e) => setFolderName(e.target.value)}
            />
          </label>
          <label className="block mb-1">
            File name
            <input
              className="input-base w-full mt-1"
              value={fileName}
              onChange={(e) => setFileName(e.target.value)}
            />
          </label>
          <hr className="my-3 border-gray-700" />
          <h4 className="font-semibold mb-1">Style</h4>
          <div className="flex space-x-2 mb-2">
            <label className="inline-flex items-center">
              Fill
              <input
                type="color"
                className="ml-2"
                value={style.fill || '#ff0000'}
                onChange={(e) => updateStyle({ fill: e.target.value })}
              />
            </label>
            <label className="inline-flex items-center">
              Outline
              <input
                type="color"
                className="ml-2"
                value={style.outline || '#000000'}
                onChange={(e) => updateStyle({ outline: e.target.value })}
              />
            </label>
          </div>
          <label className="block">
            Opacity
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              className="w-full"
              value={style.opacity ?? 0.5}
              onChange={(e) => updateStyle({ opacity: +e.target.value })}
            />
            <span className="ml-2 font-mono">{(style.opacity ?? 0.5).toFixed(2)}</span>
          </label>
          <label className="block mt-2">
            Outline weight
            <input
              type="number"
              min={0}
              max={10}
              className="input-base mt-1 w-20"
              value={style.weight ?? 2}
              onChange={(e) => updateStyle({ weight: +e.target.value })}
            />
          </label>
          {/* Results table */}
          <div className="mt-3">
            <h4 className="font-semibold mb-1">Results ({features.length})</h4>
            <div className="max-h-64 overflow-auto border border-gray-700">
              <table className="min-w-full text-xs">
                <thead>
                  <tr className="bg-gray-700 text-gray-100">
                    <th className="px-2 py-1">Select</th>
                    <th className="px-2 py-1">Lot</th>
                    <th className="px-2 py-1">Plan</th>
                  </tr>
                </thead>
                <tbody>
                  {features.map((f, i) => {
                    const p = f.properties || {};
                    const lot = p.lot ?? p.lotnumber ?? '';
                    const plan = p.plan ?? p.planlabel ?? '';
                    return (
                      <tr key={i} className={i % 2 === 0 ? 'bg-gray-800' : 'bg-gray-700'}>
                        <td className="px-2 py-1 text-center">
                          <input type="checkbox" checked={!!selected[i]} onChange={() => toggle && toggle(i)} />
                        </td>
                        <td className="px-2 py-1">{lot}</td>
                        <td className="px-2 py-1">{plan}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <div className="grid grid-cols-2 gap-2 mt-3">
              <button className="btn-primary" onClick={() => downloadWithMeta('kml')}>
                Download KML
              </button>
              <button className="btn-primary" onClick={() => downloadWithMeta('shp')}>
                Download SHP
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}