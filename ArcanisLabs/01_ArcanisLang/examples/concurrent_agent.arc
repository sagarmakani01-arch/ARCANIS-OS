# Concurrent Agent Workflow

import "std/http"
import "std/ai"
import "std/time"

agent Researcher {
    role: "Research assistant"
    model: "arcanis-research"

    tool search_web(query: String) -> String
    tool summarize(text: String) -> String

    async fn research(topic: String) -> String {
        # Parallel searches
        let results = await all([
            async self.search_web("{topic} latest developments"),
            async self.search_web("{topic} fundamentals"),
            async self.search_web("{topic} future trends")
        ])

        # Combine and summarize
        let combined = results.join("\n\n")
        return await self.summarize(combined)
    }
}

let researcher = Researcher()
let summary = await researcher.research("quantum computing")
print(summary)
