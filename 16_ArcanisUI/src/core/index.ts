export { createElement, createTextVNode, Fragment, h } from './dom/createElement';
export { diff, type DiffResult } from './dom/diff';
export { DOMRenderer } from './renderer/DOMRenderer';
export { Scheduler, scheduler } from './scheduler/Scheduler';
export {
  createInstance,
  getInstance,
  removeInstance,
  setCurrentInstance,
  getCurrentInstance,
  useState,
  useEffect,
  useMemo,
  useCallback,
  renderComponent,
  instances,
} from './component/component';
export { createApp, render, mount, type App } from './engine/engine';
