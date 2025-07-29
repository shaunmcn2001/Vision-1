import {createContext} from 'react';

/**
 * Context used to pass search state and actions to the QueryPanel embedded
 * inside the kepler.gl side panel.  By using a context we avoid drilling
 * props through multiple layers and can access the functions from the
 * `CustomSidePanelFactory` injected into kepler.gl.
 */
export const SearchContext = createContext({});