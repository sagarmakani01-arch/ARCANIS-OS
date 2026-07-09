# Documentation Generator

Generates API documentation from JSDoc comments in source code.

## Features

- **JSDoc Parsing**: Extract descriptions, tags, and type information
- **Symbol Discovery**: Automatically find exported functions, classes, interfaces, and types
- **Markdown & HTML Output**: Render documentation in either format
- **Tag Support**: Parse and display `@param`, `@returns`, `@example`, and other JSDoc tags

## Usage

```typescript
import { DocumentationGenerator } from '@arcanis/developer-tools';

const docgen = new DocumentationGenerator({
  format: 'markdown',
  outputDir: './docs/api',
  title: 'My API',
});

const sources = new Map([
  ['src/index.ts', sourceCode],
]);

const pages = await docgen.generate(sources);
const rendered = docgen.render(pages);
```

## CLI

```bash
arcanis-dev docgen --format markdown src/
arcanis-dev docgen --format html --output docs/api/ src/
```

## JSDoc Format

```typescript
/**
 * Calculate the total price with tax
 * @param price - The base price
 * @param taxRate - The tax rate (0-1)
 * @returns The total price including tax
 */
export function calculateTotal(price: number, taxRate: number): number {
  return price * (1 + taxRate);
}
```
