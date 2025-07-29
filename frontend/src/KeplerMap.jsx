import React, {useState, useEffect} from 'react';
import KeplerGl from '@kepler.gl/components';
import {injectComponents, SidePanelFactory, Icons} from '@kepler.gl/components';
import QueryPanel from './QueryPanel.jsx';

// -----------------------------------------------------------------------------
// Custom SidePanel injection
//
// We wrap the default SidePanelFactory exported by kepler.gl and append a
// bespoke "Query" tab.  The injected tab uses the `<QueryPanel>` component
// defined in QueryPanel.jsx.  By leveraging the `injectComponents` API we can
// extend kepler.gl’s UI without forking its code.

function CustomSidePanelFactory(...deps) {
  // Instantiate the original side panel
  const SidePanel = SidePanelFactory(...deps);
  const CustomSidePanel = (props) => {
    const newPanels = [
      ...props.panels,
      {
        id: 'query',
        label: 'Query',
        // Choose a search icon for our tab
        iconComponent: Icons.Search,
        // Render QueryPanel; QueryPanel reads actions/state from context
        component: () => <QueryPanel />, // eslint-disable-line react/display-name
      },
    ];
    return <SidePanel {...props} panels={newPanels} />;
  };
  return CustomSidePanel;
}
// Copy dependency list so kepler.gl can resolve dependencies of our factory
CustomSidePanelFactory.deps = SidePanelFactory.deps;

// Create a new KeplerGl component with our side panel injected
const KeplerGlInjected = injectComponents([
  [SidePanelFactory, CustomSidePanelFactory],
]);

/**
 * KeplerMap wraps the kepler.gl map component.  It automatically resizes
 * according to the window dimensions and uses the injected SidePanel which
 * includes the Query tab.
 */
export default function KeplerMap() {
  const [dims, setDims] = useState({ width: 0, height: 0 });
  useEffect(() => {
    // Update size on mount and whenever the window is resized
    const update = () => {
      setDims({ width: window.innerWidth, height: window.innerHeight });
    };
    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);

  const token = import.meta.env.VITE_MAPBOX_TOKEN || '';
  return (
    <div style={{ position: 'relative', flex: 1 }}>
      <KeplerGlInjected
        id="parcels"
        mapboxApiAccessToken={token}
        width={dims.width}
        height={dims.height}
      />
    </div>
  );
}