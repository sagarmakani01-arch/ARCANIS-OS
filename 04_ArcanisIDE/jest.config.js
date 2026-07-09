module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  testMatch: ['**/tests/**/*.test.ts'],
  moduleNameMapper: {
    '^@core/(.*)$': '<rootDir>/src/core/$1',
    '^@editor/(.*)$': '<rootDir>/src/editor/$1',
    '^@ai/(.*)$': '<rootDir>/src/ai/$1',
    '^@tools/(.*)$': '<rootDir>/src/tools/$1',
    '^@ui/(.*)$': '<rootDir>/src/ui/$1',
    '^@api/(.*)$': '<rootDir>/src/api/$1',
  },
  transform: {
    '^.+\\.ts$': ['ts-jest', {
      tsconfig: 'tsconfig.json',
    }],
  },
};
