# Getting Started with ArcanisOS

## Installation

### Prerequisites
- Node.js 18+
- npm 9+

### Quick Install
```bash
git clone <repo-url> arcanis-os
cd arcanis-os
npm install
npm run build
```

### Run Tests
```bash
npm test
```

### Start the OS
```bash
npm start
```

## Using ArcanisOS

### Shell Commands
```
arcanis@os:/home/user$ help
arcanis@os:/home/user$ echo Hello Arcanis
arcanis@os:/home/user$ ai
arcanis@os:/home/user$ What files are in my home directory?
arcanis@os:/home/user$ exit
```

### AI Mode
Toggle AI mode with the `ai` command. In AI mode, the shell interprets natural language directly through ArcanisBrain.

### Development
```typescript
import ArcanisOS from "arcanis-os";

const os = new ArcanisOS();
await os.boot();

// Execute commands naturally
await os.executeCommand("create a new project called my-app");

// Use the AI directly
const thought = await os.brain.think("What can you do?");
console.log(thought.content);

// Manage memory
os.brain.memory.store("user_preference", { theme: "dark" });

// Shutdown
await os.shutdown();
```

## Custom Install

```bash
node installer/index.js --prefix /custom/path
```
