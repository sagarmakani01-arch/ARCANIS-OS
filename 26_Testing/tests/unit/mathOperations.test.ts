// Sample Unit Tests for ArcanisTesting Framework

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { assert } from '../../src/core/assertions';

// Sample utility functions to test
const add = (a: number, b: number): number => a + b;
const subtract = (a: number, b: number): number => a - b;
const multiply = (a: number, b: number): number => a * b;
const divide = (a: number, b: number): number => {
  if (b === 0) {
    throw new Error('Division by zero');
  }
  return a / b;
};

const isEven = (num: number): boolean => !isNaN(num) && num % 2 === 0;
const isOdd = (num: number): boolean => !isNaN(num) && num % 2 !== 0;

const factorial = (n: number): number => {
  if (n < 0) {
    throw new Error('Factorial is not defined for negative numbers');
  }
  if (n === 0 || n === 1) {
    return 1;
  }
  return n * factorial(n - 1);
};

const fibonacci = (n: number): number => {
  if (n < 0) {
    throw new Error('Fibonacci is not defined for negative numbers');
  }
  if (n === 0) return 0;
  if (n === 1) return 1;
  return fibonacci(n - 1) + fibonacci(n - 2);
};

// Test suite
describe('Math Operations', () => {
  beforeEach(() => {
    // Setup before each test
    console.log('  Setting up test...');
  });

  afterEach(() => {
    // Cleanup after each test
    console.log('  Cleaning up test...');
  });

  describe('add', () => {
    it('should add two positive numbers', () => {
      expect(add(2, 3)).toBe(5);
    });

    it('should add two negative numbers', () => {
      expect(add(-2, -3)).toBe(-5);
    });

    it('should add positive and negative numbers', () => {
      expect(add(2, -3)).toBe(-1);
    });

    it('should handle zero', () => {
      expect(add(5, 0)).toBe(5);
    });
  });

  describe('subtract', () => {
    it('should subtract two numbers', () => {
      expect(subtract(5, 3)).toBe(2);
    });

    it('should handle negative results', () => {
      expect(subtract(3, 5)).toBe(-2);
    });
  });

  describe('multiply', () => {
    it('should multiply two numbers', () => {
      expect(multiply(4, 3)).toBe(12);
    });

    it('should handle zero', () => {
      expect(multiply(5, 0)).toBe(0);
    });

    it('should handle negative numbers', () => {
      expect(multiply(-2, 3)).toBe(-6);
    });
  });

  describe('divide', () => {
    it('should divide two numbers', () => {
      expect(divide(10, 2)).toBe(5);
    });

    it('should handle decimal results', () => {
      expect(divide(10, 3)).toBeCloseTo(3.333, 2);
    });

    it('should throw error for division by zero', () => {
      expect(() => divide(10, 0)).toThrow('Division by zero');
    });
  });
});

describe('Number Utilities', () => {
  describe('isEven', () => {
    it('should return true for even numbers', () => {
      expect(isEven(2)).toBe(true);
      expect(isEven(4)).toBe(true);
      expect(isEven(0)).toBe(true);
    });

    it('should return false for odd numbers', () => {
      expect(isEven(1)).toBe(false);
      expect(isEven(3)).toBe(false);
      expect(isEven(-1)).toBe(false);
    });
  });

  describe('isOdd', () => {
    it('should return true for odd numbers', () => {
      expect(isOdd(1)).toBe(true);
      expect(isOdd(3)).toBe(true);
      expect(isOdd(-1)).toBe(true);
    });

    it('should return false for even numbers', () => {
      expect(isOdd(2)).toBe(false);
      expect(isOdd(4)).toBe(false);
      expect(isOdd(0)).toBe(false);
    });
  });
});

describe('Advanced Math Functions', () => {
  describe('factorial', () => {
    it('should calculate factorial of 0', () => {
      expect(factorial(0)).toBe(1);
    });

    it('should calculate factorial of 1', () => {
      expect(factorial(1)).toBe(1);
    });

    it('should calculate factorial of 5', () => {
      expect(factorial(5)).toBe(120);
    });

    it('should calculate factorial of 10', () => {
      expect(factorial(10)).toBe(3628800);
    });

    it('should throw error for negative numbers', () => {
      expect(() => factorial(-1)).toThrow('Factorial is not defined for negative numbers');
    });
  });

  describe('fibonacci', () => {
    it('should return 0 for n=0', () => {
      expect(fibonacci(0)).toBe(0);
    });

    it('should return 1 for n=1', () => {
      expect(fibonacci(1)).toBe(1);
    });

    it('should return 1 for n=2', () => {
      expect(fibonacci(2)).toBe(1);
    });

    it('should return 5 for n=5', () => {
      expect(fibonacci(5)).toBe(5);
    });

    it('should return 55 for n=10', () => {
      expect(fibonacci(10)).toBe(55);
    });

    it('should throw error for negative numbers', () => {
      expect(() => fibonacci(-1)).toThrow('Fibonacci is not defined for negative numbers');
    });
  });
});

describe('Edge Cases', () => {
  it('should handle very large numbers', () => {
    expect(add(Number.MAX_SAFE_INTEGER, 1)).toBe(Number.MAX_SAFE_INTEGER + 1);
  });

  it('should handle very small numbers', () => {
    expect(add(Number.MIN_SAFE_INTEGER, -1)).toBe(Number.MIN_SAFE_INTEGER - 1);
  });

  it('should handle floating point numbers', () => {
    expect(add(0.1, 0.2)).toBeCloseTo(0.3, 10);
  });

  it('should handle special values', () => {
    expect(isEven(NaN)).toBe(false);
    expect(isOdd(NaN)).toBe(false);
  });
});

describe('Performance Tests', () => {
  it('should add numbers quickly', () => {
    const start = performance.now();
    for (let i = 0; i < 1000000; i++) {
      add(i, i + 1);
    }
    const duration = performance.now() - start;
    expect(duration).toBeLessThan(1000); // Should complete in less than 1 second
  });

  it('should calculate factorial quickly', () => {
    const start = performance.now();
    factorial(20);
    const duration = performance.now() - start;
    expect(duration).toBeLessThan(100); // Should complete in less than 100ms
  });
});

// Export test functions for external use
export {
  add,
  subtract,
  multiply,
  divide,
  isEven,
  isOdd,
  factorial,
  fibonacci,
};
