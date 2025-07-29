import React, {useState, useMemo} from 'react';
import KeplerMap from './KeplerMap.jsx';
import {SearchContext} from './SearchContext.js';
import {useDispatch} from 'react-redux';
import {addDataToMap} from '@kepler.gl/actions';
import {processGeojson} from '@kepler.gl/processors';

/**
 * Top level application component.
 *
 * It maintains parcel features, selection state and styling options.  When
 * search results change, it dispatches an `addDataToMap` action to kepler.gl
 * so the polygons appear on the map.  All search related state and actions
 * are provided to the QueryPanel via the SearchContext.
 */
export default function App() {
  const dispatch = useDispatch();
  const [features, setFeatures] = useState([]);
  const [selected, setSelected] = useState({});
  const [style, setStyle] = useState({
    fill: '#ff0000',
    outline: '#000000',
    opacity: 0.5,
    weight: 2,
  });

  // Whenever features change, push them into kepler.gl
  React.useEffect(() => {
    if (features.length) {
      const geojson = { type: 'FeatureCollection', features };
      const data = processGeojson(geojson);
      dispatch(
        addDataToMap({
          datasets: {
            info: { label: 'Parcels', id: 'parcels' },
            data,
          },
          option: { centerMap: true, readOnly: false },
        }),
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [features]);

  const onResults = (feats) => {
    setFeatures(feats);
    setSelected({});
  };
  const toggle = (idx) => {
    setSelected((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };
  const download = async (type, folderName, fileName) => {
    const base = import.meta.env.VITE_API_BASE || '';
    const chosen = Object.keys(selected).length
      ? features.filter((_, i) => selected[i])
      : features;
    // Include style in the download request when performing KML exports.
    // The style state is captured from the QueryPanel via SearchContext.  It
    // contains fill/outline colours (hex), opacity and weight.  Pass it
    // through to the back‑end where supported; unknown keys will be
    // ignored.
    const body = { features: chosen, folderName, fileName, style };
    const url = `${base}/download/${type}`;
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      // eslint-disable-next-line no-alert
      alert(`Failed to download ${type.toUpperCase()}: ${r.status}`);
      return;
    }
    const blob = await r.blob();
    const objectUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = objectUrl;
    a.download = fileName || (type === 'kml' ? 'parcels.kml' : 'parcels.zip');
    a.click();
    window.URL.revokeObjectURL(objectUrl);
  };

  const value = useMemo(
    () => ({
      onResults,
      features,
      selected,
      toggle,
      download,
      style,
      setStyle,
    }),
    [features, selected, style],
  );

  return (
    <SearchContext.Provider value={value}>
      <div className="h-full w-full">
        <KeplerMap />
      </div>
    </SearchContext.Provider>
  );
}