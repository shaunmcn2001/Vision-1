import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import createStore from './store.js';
import {Provider} from 'react-redux';
import './index.css';

// Initialise Redux store.  The store includes the kepler.gl reducer and
// applies the task middleware required by kepler.gl.  See store.js for details.
const store = createStore();

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Provider store={store}>
      <App />
    </Provider>
  </React.StrictMode>,
);