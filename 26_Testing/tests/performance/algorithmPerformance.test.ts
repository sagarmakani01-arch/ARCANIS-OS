// Sample Performance Tests for ArcanisTesting Framework

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { benchmark, compareBenchmarks } from '../../src/testing/performance/performanceTest';
import { assert } from '../../../src/core/assertions';

// Sample functions to benchmark
const fibonacci = (n: number): number => {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
};

const fibonacciIterative = (n: number): number => {
  if (n <= 1) return n;
  let a = 0, b = 1;
  for (let i = 2; i <= n; i++) {
    [a, b] = [b, a + b];
  }
  return b;
};

const sortArray = (arr: number[]): number[] => {
  return [...arr].sort((a, b) => a - b);
};

const bubbleSort = (arr: number[]): number[] => {
  const result = [...arr];
  for (let i = 0; i < result.length; i++) {
    for (let j = 0; j < result.length - i - 1; j++) {
      if (result[j] > result[j + 1]) {
        [result[j], result[j + 1]] = [result[j + 1], result[j]];
      }
    }
  }
  return result;
};

const binarySearch = (arr: number[], target: number): number => {
  let left = 0;
  let right = arr.length - 1;
  
  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    if (arr[mid] === target) return mid;
    if (arr[mid] < target) left = mid + 1;
    else right = mid - 1;
  }
  
  return -1;
};

const linearSearch = (arr: number[], target: number): number => {
  for (let i = 0; i < arr.length; i++) {
    if (arr[i] === target) return i;
  }
  return -1;
};

// Sample data structures
class LinkedList<T> {
  private head: { value: T; next: LinkedList<T>['head'] } | null = null;

  push(value: T): void {
    this.head = { value, next: this.head };
  }

  find(predicate: (value: T) => boolean): T | null {
    let current = this.head;
    while (current) {
      if (predicate(current.value)) return current.value;
      current = current.next;
    }
    return null;
  }

  toArray(): T[] {
    const result: T[] = [];
    let current = this.head;
    while (current) {
      result.push(current.value);
      current = current.next;
    }
    return result;
  }
}

class HashMap<K, V> {
  private map: Map<K, V> = new Map();

  set(key: K, value: V): void {
    this.map.set(key, value);
  }

  get(key: K): V | undefined {
    return this.map.get(key);
  }

  has(key: K): boolean {
    return this.map.has(key);
  }

  delete(key: K): boolean {
    return this.map.delete(key);
  }

  get size(): number {
    return this.map.size;
  }
}

describe('Algorithm Performance Tests', () => {
  describe('Fibonacci Implementation', () => {
    it('should compare recursive vs iterative performance', async () => {
      // Arrange
      const n = 30;

      // Act
      const recursiveResult = await benchmark('Recursive Fibonacci', async () => {
        fibonacci(n);
      }, 10);

      const iterativeResult = await benchmark('Iterative Fibonacci', async () => {
        fibonacciIterative(n);
      }, 10);

      // Assert
      expect(recursiveResult.avg).toBeGreaterThan(0);
      expect(iterativeResult.avg).toBeGreaterThan(0);
      
      // Iterative should be significantly faster
      expect(iterativeResult.avg).toBeLessThan(recursiveResult.avg);
    });

    it('should handle edge cases efficiently', async () => {
      // Arrange & Act
      const edgeCases = [0, 1, 2, 10, 20];
      
      for (const n of edgeCases) {
        const result = await benchmark(`Fibonacci(${n})`, async () => {
          fibonacciIterative(n);
        }, 100);
        
        // Assert
        expect(result.avg).toBeLessThan(1); // Should complete in less than 1ms
      }
    });
  });

  describe('Sorting Algorithms', () => {
    it('should compare built-in sort vs bubble sort', async () => {
      // Arrange
      const sizes = [100, 1000, 5000];
      
      for (const size of sizes) {
        const arr = Array.from({ length: size }, () => Math.floor(Math.random() * size));

        // Act
        const builtinResult = await benchmark(`Built-in Sort (${size} elements)`, async () => {
          sortArray(arr);
        }, 10);

        const bubbleResult = await benchmark(`Bubble Sort (${size} elements)`, async () => {
          bubbleSort(arr);
        }, 5);

        // Assert
        expect(builtinResult.avg).toBeGreaterThan(0);
        expect(bubbleResult.avg).toBeGreaterThan(0);
        
        // Built-in sort should be faster for larger arrays
        if (size >= 1000) {
          expect(builtinResult.avg).toBeLessThan(bubbleResult.avg);
        }
      }
    });

    it('should handle already sorted arrays', async () => {
      // Arrange
      const sortedArr = Array.from({ length: 1000 }, (_, i) => i);

      // Act
      const result = await benchmark('Sort Already Sorted', async () => {
        sortArray(sortedArr);
      }, 10);

      // Assert
      expect(result.avg).toBeLessThan(10); // Should be fast
    });

    it('should handle reverse sorted arrays', async () => {
      // Arrange
      const reverseArr = Array.from({ length: 1000 }, (_, i) => 1000 - i);

      // Act
      const result = await benchmark('Sort Reverse Sorted', async () => {
        sortArray(reverseArr);
      }, 10);

      // Assert
      expect(result.avg).toBeGreaterThan(0);
    });
  });

  describe('Search Algorithms', () => {
    it('should compare binary search vs linear search', async () => {
      // Arrange
      const size = 10000;
      const sortedArr = Array.from({ length: size }, (_, i) => i);
      const target = Math.floor(size / 2);

      // Act
      const binaryResult = await benchmark('Binary Search', async () => {
        binarySearch(sortedArr, target);
      }, 1000);

      const linearResult = await benchmark('Linear Search', async () => {
        linearSearch(sortedArr, target);
      }, 100);

      // Assert
      expect(binaryResult.avg).toBeGreaterThan(0);
      expect(linearResult.avg).toBeGreaterThan(0);
      
      // Binary search should be significantly faster
      expect(binaryResult.avg).toBeLessThan(linearResult.avg);
    });

    it('should handle different target positions', async () => {
      // Arrange
      const size = 10000;
      const sortedArr = Array.from({ length: size }, (_, i) => i);
      const targets = [0, size / 4, size / 2, (3 * size) / 4, size - 1];

      for (const target of targets) {
        // Act
        const result = await benchmark(`Binary Search (target: ${target})`, async () => {
          binarySearch(sortedArr, target);
        }, 1000);

        // Assert
        expect(result.avg).toBeLessThan(1); // Should be very fast
      }
    });
  });
});

describe('Data Structure Performance Tests', () => {
  describe('Array vs LinkedList', () => {
    it('should compare insertion performance', async () => {
      // Arrange
      const size = 10000;

      // Act
      const arrayResult = await benchmark('Array Push', async () => {
        const arr: number[] = [];
        for (let i = 0; i < size; i++) {
          arr.push(i);
        }
      }, 10);

      const linkedListResult = await benchmark('LinkedList Push', async () => {
        const list = new LinkedList<number>();
        for (let i = 0; i < size; i++) {
          list.push(i);
        }
      }, 10);

      // Assert
      expect(arrayResult.avg).toBeGreaterThan(0);
      expect(linkedListResult.avg).toBeGreaterThan(0);
    });

    it('should compare search performance', async () => {
      // Arrange
      const size = 10000;
      const target = Math.floor(size / 2);

      // Create data structures
      const arr = Array.from({ length: size }, (_, i) => i);
      const list = new LinkedList<number>();
      for (let i = 0; i < size; i++) {
        list.push(i);
      }

      // Act
      const arrayResult = await benchmark('Array Find', async () => {
        arr.find(x => x === target);
      }, 100);

      const linkedListResult = await benchmark('LinkedList Find', async () => {
        list.find(x => x === target);
      }, 10);

      // Assert
      expect(arrayResult.avg).toBeGreaterThan(0);
      expect(linkedListResult.avg).toBeGreaterThan(0);
    });
  });

  describe('Map vs Object', () => {
    it('should compare insertion performance', async () => {
      // Arrange
      const size = 10000;

      // Act
      const mapResult = await benchmark('Map Set', async () => {
        const map = new Map<number, string>();
        for (let i = 0; i < size; i++) {
          map.set(i, `value${i}`);
        }
      }, 10);

      const objectResult = await benchmark('Object Assignment', async () => {
        const obj: Record<number, string> = {};
        for (let i = 0; i < size; i++) {
          obj[i] = `value${i}`;
        }
      }, 10);

      // Assert
      expect(mapResult.avg).toBeGreaterThan(0);
      expect(objectResult.avg).toBeGreaterThan(0);
    });

    it('should compare lookup performance', async () => {
      // Arrange
      const size = 10000;
      const target = Math.floor(size / 2);

      // Create data structures
      const map = new Map<number, string>();
      const obj: Record<number, string> = {};
      for (let i = 0; i < size; i++) {
        map.set(i, `value${i}`);
        obj[i] = `value${i}`;
      }

      // Act
      const mapResult = await benchmark('Map Get', async () => {
        map.get(target);
      }, 1000);

      const objectResult = await benchmark('Object Access', async () => {
        obj[target];
      }, 1000);

      // Assert
      expect(mapResult.avg).toBeGreaterThan(0);
      expect(objectResult.avg).toBeGreaterThan(0);
    });
  });
});

describe('Memory Performance Tests', () => {
  it('should handle large data structures efficiently', async () => {
    // Arrange
    const size = 1000000;

    // Act
    const result = await benchmark('Large Array Creation', async () => {
      const arr = new Array(size);
      for (let i = 0; i < size; i++) {
        arr[i] = i;
      }
    }, 5);

    // Assert
    expect(result.avg).toBeGreaterThan(0);
  });

  it('should handle object creation efficiently', async () => {
    // Arrange
    const size = 100000;

    // Act
    const result = await benchmark('Object Creation', async () => {
      const objects = [];
      for (let i = 0; i < size; i++) {
        objects.push({ id: i, name: `item${i}` });
      }
    }, 5);

    // Assert
    expect(result.avg).toBeGreaterThan(0);
  });
});

describe('Concurrency Performance Tests', () => {
  it('should handle concurrent operations', async () => {
    // Arrange
    const concurrency = 5;
    const operationsPerThread = 100;

    // Act
    const startTime = performance.now();
    const promises = Array(concurrency).fill(null).map(async () => {
      for (let i = 0; i < operationsPerThread; i++) {
        // Simulate some work
        await new Promise(resolve => setTimeout(resolve, 0));
      }
    });
    await Promise.all(promises);
    const duration = performance.now() - startTime;

    // Assert
    expect(duration).toBeGreaterThan(0);
    console.log(`Concurrent operations completed in ${duration.toFixed(2)}ms`);
  }, 15000);

  it('should scale with increased concurrency', async () => {
    // Arrange
    const concurrencies = [1, 2, 4, 8];
    const results: { concurrency: number; duration: number }[] = [];

    // Act
    for (const concurrency of concurrencies) {
      const startTime = performance.now();
      const promises = Array(concurrency).fill(null).map(async () => {
        for (let i = 0; i < 1000; i++) {
          // Simulate work
          fibonacciIterative(20);
        }
      });
      await Promise.all(promises);
      const duration = performance.now() - startTime;
      results.push({ concurrency, duration });
    }

    // Assert
    expect(results.length).toBe(concurrencies.length);
    results.forEach(r => expect(r.duration).toBeGreaterThan(0));
  });
});

describe('Load Testing', () => {
  it('should handle sustained load', async () => {
    // Arrange
    const duration = 1000; // 1 second
    const startTime = performance.now();
    let operationCount = 0;

    // Act
    while (performance.now() - startTime < duration) {
      fibonacciIterative(20);
      operationCount++;
    }

    const actualDuration = performance.now() - startTime;
    const operationsPerSecond = operationCount / (actualDuration / 1000);

    // Assert
    expect(operationCount).toBeGreaterThan(0);
    expect(operationsPerSecond).toBeGreaterThan(100);
    console.log(`Load test: ${operationsPerSecond.toFixed(0)} operations/second`);
  }, 15000);

  it('should maintain performance under load', async () => {
    // Arrange
    const iterations = 100;
    const durations: number[] = [];

    // Act
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      fibonacciIterative(20);
      durations.push(performance.now() - start);
    }

    // Assert
    const avgDuration = durations.reduce((a, b) => a + b, 0) / durations.length;
    const maxDuration = Math.max(...durations);
    
    expect(avgDuration).toBeLessThan(1); // Average should be less than 1ms
    expect(maxDuration).toBeLessThan(5); // Max should be less than 5ms
  });
});
