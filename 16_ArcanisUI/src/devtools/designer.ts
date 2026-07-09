export interface DesignerConfig {
  enabled: boolean;
  snapToGrid: boolean;
  gridSize: number;
  showGuides: boolean;
  showOutlines: boolean;
}

export interface DesignElement {
  id: string;
  type: string;
  x: number;
  y: number;
  width: number;
  height: number;
  parentId: string | null;
  styles: Record<string, string>;
  props: Record<string, unknown>;
  children: string[];
}

export interface DesignerState {
  elements: Map<string, DesignElement>;
  selectedId: string | null;
  hoveredId: string | null;
  zoom: number;
  panX: number;
  panY: number;
}

export interface UIDesigner {
  createElement(type: string, x: number, y: number, width: number, height: number): DesignElement;
  updateElement(id: string, updates: Partial<DesignElement>): void;
  deleteElement(id: string): void;
  selectElement(id: string | null): void;
  moveElement(id: string, x: number, y: number): void;
  resizeElement(id: string, width: number, height: number): void;
  getElement(id: string): DesignElement | undefined;
  getAllElements(): DesignElement[];
  exportJSON(): string;
  importJSON(json: string): void;
  zoomTo(level: number): void;
  panTo(x: number, y: number): void;
}

export function createDesigner(config: DesignerConfig): UIDesigner {
  let state: DesignerState = {
    elements: new Map(),
    selectedId: null,
    hoveredId: null,
    zoom: 1,
    panX: 0,
    panY: 0,
  };

  let idCounter = 0;

  function snapToGrid(value: number): number {
    if (!config.snapToGrid) return value;
    return Math.round(value / config.gridSize) * config.gridSize;
  }

  function generateId(): string {
    return `design-${++idCounter}`;
  }

  return {
    createElement(type, x, y, width, height) {
      const id = generateId();
      const element: DesignElement = {
        id,
        type,
        x: snapToGrid(x),
        y: snapToGrid(y),
        width: snapToGrid(width),
        height: snapToGrid(height),
        parentId: null,
        styles: {},
        props: {},
        children: [],
      };
      state.elements.set(id, element);
      return element;
    },

    updateElement(id, updates) {
      const element = state.elements.get(id);
      if (!element) return;
      Object.assign(element, updates);
    },

    deleteElement(id) {
      const element = state.elements.get(id);
      if (!element) return;

      if (element.parentId) {
        const parent = state.elements.get(element.parentId);
        if (parent) {
          parent.children = parent.children.filter((childId) => childId !== id);
        }
      }

      element.children.forEach((childId) => this.deleteElement(childId));
      state.elements.delete(id);
      if (state.selectedId === id) state.selectedId = null;
    },

    selectElement(id) {
      state.selectedId = id;
    },

    moveElement(id, x, y) {
      const element = state.elements.get(id);
      if (!element) return;
      element.x = snapToGrid(x);
      element.y = snapToGrid(y);
    },

    resizeElement(id, width, height) {
      const element = state.elements.get(id);
      if (!element) return;
      element.width = snapToGrid(width);
      element.height = snapToGrid(height);
    },

    getElement: (id) => state.elements.get(id),
    getAllElements: () => Array.from(state.elements.values()),

    exportJSON() {
      const data = {
        elements: Array.from(state.elements.values()),
        config,
        version: '1.0.0',
      };
      return JSON.stringify(data, null, 2);
    },

    importJSON(json) {
      const data = JSON.parse(json);
      state.elements.clear();
      data.elements.forEach((el: DesignElement) => {
        state.elements.set(el.id, el);
      });
    },

    zoomTo(level) {
      state.zoom = Math.max(0.1, Math.min(5, level));
    },

    panTo(x, y) {
      state.panX = x;
      state.panY = y;
    },
  };
}
