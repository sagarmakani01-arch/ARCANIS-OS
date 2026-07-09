"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TestingTools = exports.spyOn = exports.createMock = exports.expect = exports.throws = exports.deepEqual = exports.equal = exports.assert = exports.TestRunner = void 0;
const runner_js_1 = require("./runner.js");
Object.defineProperty(exports, "TestRunner", { enumerable: true, get: function () { return runner_js_1.TestRunner; } });
const assert_js_1 = require("./assert.js");
Object.defineProperty(exports, "assert", { enumerable: true, get: function () { return assert_js_1.assert; } });
Object.defineProperty(exports, "equal", { enumerable: true, get: function () { return assert_js_1.equal; } });
Object.defineProperty(exports, "deepEqual", { enumerable: true, get: function () { return assert_js_1.deepEqual; } });
Object.defineProperty(exports, "throws", { enumerable: true, get: function () { return assert_js_1.throws; } });
Object.defineProperty(exports, "expect", { enumerable: true, get: function () { return assert_js_1.expect; } });
const mock_js_1 = require("./mock.js");
Object.defineProperty(exports, "createMock", { enumerable: true, get: function () { return mock_js_1.createMock; } });
Object.defineProperty(exports, "spyOn", { enumerable: true, get: function () { return mock_js_1.spyOn; } });
class TestingTools {
    runner;
    constructor() {
        this.runner = new runner_js_1.TestRunner();
    }
    async runTests(suiteName, testFn) {
        this.runner.describe(suiteName, testFn);
        return this.runner.run();
    }
    assert = assert_js_1.assert;
    equal = assert_js_1.equal;
    deepEqual = assert_js_1.deepEqual;
    throws = assert_js_1.throws;
    expect = assert_js_1.expect;
    createMock = mock_js_1.createMock;
    spyOn = mock_js_1.spyOn;
}
exports.TestingTools = TestingTools;
//# sourceMappingURL=index.js.map