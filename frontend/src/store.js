import {createStore as reduxCreateStore, combineReducers, applyMiddleware, compose} from 'redux';
import keplerGlReducer from '@kepler.gl/reducers';
import {taskMiddleware} from 'react-palm/tasks';

/**
 * Construct and return a Redux store configured for kepler.gl.
 *
 * kepler.gl relies on Redux for state management and side effects via
 * react‑palm.  We mount the `keplerGl` reducer at the root of our
 * reducers tree and apply the `taskMiddleware` so asynchronous actions
 * dispatched by kepler.gl are executed properly.  If you wish to add
 * your own reducers, include them in the combineReducers call.
 */
export default function createStore() {
  const reducers = combineReducers({
    keplerGl: keplerGlReducer,
    // You can add other reducers here e.g. search results state
  });
  const middlewares = [taskMiddleware];
  const enhancers = compose(applyMiddleware(...middlewares));
  return reduxCreateStore(reducers, {}, enhancers);
}