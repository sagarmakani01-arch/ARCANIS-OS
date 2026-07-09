"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.createMock = createMock;
exports.spyOn = spyOn;
function createMock(implementation) {
    const mock = { calls: [], returns: undefined };
    const fn = ((...args) => {
        mock.calls.push(args);
        const result = mock.implementation ? mock.implementation(...args) : mock.returns;
        return result;
    });
    mock.calls = [];
    Object.defineProperty(fn, 'calls', { get: () => mock.calls });
    Object.defineProperty(fn, 'returns', {
        get: () => mock.returns,
        set: (v) => { mock.returns = v; },
    });
    Object.defineProperty(fn, 'implementation', {
        get: () => mock.implementation,
        set: (v) => { mock.implementation = v; },
    });
    return fn;
}
function spyOn(obj, method) {
    const original = obj[method];
    const mock = createMock(original);
    obj[method] = mock;
    return mock;
}
//# sourceMappingURL=mock.js.map