# ArcanisLabs Dependency Map

## Dependency Rules

1. Projects may only depend on projects with a **lower number** (earlier in the stack).
2. No **circular dependencies** are permitted.
3. Dependencies should be **explicit** and **minimal**.
4. Foundation projects (00, 24-30) are available to **all** projects.

## Dependency Table

| # | Project | Depends On | Description |
|---|---------|------------|-------------|
| 00 | Documentation | — | Standalone |
| 01 | ArcanisLang | 00, 24, 25, 26 | Language specification and implementation |
| 02 | ArcanisCompiler | 01, 00, 24, 25, 26 | Compiles ArcanisLang |
| 03 | ArcanisVM | 02, 00, 24, 25, 26 | Executes compiled bytecode |
| 04 | ArcanisIDE | 01, 02, 03, 00, 24, 25, 26 | Development environment |
| 05 | ArcanisBuild | 01, 02, 03, 00, 24, 25, 26 | Build automation |
| 06 | ArcanisPackageManager | 05, 00, 24, 25, 26 | Package distribution |
| 07 | ArcanisDatabase | 00, 24, 25, 26 | Storage engine |
| 08 | ArcanisKnowledgeGraph | 07, 00, 24, 25, 26 | Knowledge relationships |
| 09 | ArcanisBrain | 07, 08, 00, 24, 25, 26 | Central AI |
| 10 | ArcanisAgents | 09, 11, 00, 24, 25, 26 | Multi-agent system |
| 11 | ArcanisMemory | 07, 00, 24, 25, 26 | Long-term memory |
| 12 | ArcanisShell | 09, 00, 24, 25, 26 | Command interface |
| 13 | ArcanisAutomation | 09, 10, 00, 24, 25, 26 | Workflow automation |
| 14 | ArcanisVoice | 09, 00, 24, 25, 26 | Voice interaction |
| 15 | ArcanisVision | 09, 00, 24, 25, 26 | Computer vision |
| 16 | ArcanisUI | 00, 24, 25, 26 | Interface framework |
| 17 | ArcanisDesktop | 16, 09, 10, 00, 24, 25, 26 | Desktop environment |
| 18 | ArcanisKernel | 00, 24, 25, 26 | OS kernel |
| 19 | ArcanisDrivers | 18, 00, 24, 25, 26 | Hardware drivers |
| 20 | ArcanisFileSystem | 18, 07, 08, 00, 24, 25, 26 | Intelligent filesystem |
| 21 | ArcanisNetwork | 18, 00, 24, 25, 26 | Networking stack |
| 22 | ArcanisSecurity | 18, 00, 24, 25, 26 | Security framework |
| 23 | ArcanisOS | 17, 18, 19, 20, 21, 22, 00, 24, 25, 26 | Complete OS |
| 24 | SharedLibraries | 00, 26 | Reusable components |
| 25 | DeveloperTools | 01-06, 24, 00, 26 | Developer utilities |
| 26 | Testing | 00 | Testing framework |
| 27 | Experiments | 00, 24 | Experimental projects |
| 28 | Research | 00 | Research knowledge base |
| 29 | Assets | 00 | Shared resources |
| 30 | Scripts | 00 | Automation scripts |

## Dependency Diagram

```
                 30_Scripts
                     │
    ┌───────────────┼───────────────┐
    │               │               │
 24_SharedLibs  25_DevTools     26_Testing
    │               │               │
    └───────────────┼───────────────┘
                    │
     ┌──────────────┼──────────────┐
     │              │              │
  01_Lang ──► 02_Compiler ──► 03_VM
     │              │              │
     ├──────────────┼──────────────┤
     │              │              │
  04_IDE        05_Build ──► 06_PkgMgr
     │              │
     └──────┬───────┘
            │
       07_Database ──► 08_KnowledgeGraph
            │
        09_Brain ──┬── 10_Agents
            │      ├── 11_Memory
            │      ├── 12_Shell
            │      ├── 13_Automation
            │      ├── 14_Voice
            │      └── 15_Vision
            │
        16_UI ──► 17_Desktop
            │
    ┌───────┼───────┐
    │       │       │
 18_Kernel  │       │
    │       │       │
 19_Drivers│       │
    │       │       │
 20_FS ────┤       │
    │       │       │
 21_Network│       │
    │       │       │
 22_Security│       │
    │       │       │
    └───────┴───────┘
            │
        23_ArcanisOS
```

## Build Order

The ecosystem must be built in this order (within each phase, projects can be built in parallel):

1. 00_Documentation, 24_SharedLibraries, 26_Testing, 30_Scripts
2. 25_DeveloperTools, 27_Experiments, 28_Research, 29_Assets
3. 01_ArcanisLang
4. 02_ArcanisCompiler
5. 03_ArcanisVM
6. 04_ArcanisIDE, 05_ArcanisBuild (parallel)
7. 06_ArcanisPackageManager
8. 07_ArcanisDatabase
9. 08_ArcanisKnowledgeGraph
10. 09_ArcanisBrain, 11_ArcanisMemory, 16_ArcanisUI (parallel)
11. 10_ArcanisAgents, 12_ArcanisShell, 13_ArcanisAutomation, 14_ArcanisVoice, 15_ArcanisVision (parallel)
12. 17_ArcanisDesktop
13. 18_ArcanisKernel
14. 19_ArcanisDrivers, 20_ArcanisFileSystem, 21_ArcanisNetwork, 22_ArcanisSecurity (parallel)
15. 23_ArcanisOS
