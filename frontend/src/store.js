import {createStore as reduxCreateStore, combineReducers, applyMiddleware, compose} from 'redux';
import keplerGlReducer from '@kepler.gl/reducers';
import {enhanceReduxMiddleware} from '@kepler.gl/middleware';

export default function createStore() {
  const reducers = combineReducers({ keplerGl: keplerGlReducer });
  const middlewares = enhanceReduxMiddleware([]);
  const enhancers = compose(applyMiddleware(...middlewares));
  return reduxCreateStore(reducers, {}, enhancers);
}
