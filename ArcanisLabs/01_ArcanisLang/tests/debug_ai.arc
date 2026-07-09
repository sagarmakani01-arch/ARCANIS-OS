# AI-Powered Assistant

agent Assistant {
    role: "Helpful assistant"
    model: "arcanis-default"
    memory: true

    tool get_time() -> String
    tool calculate(expr: String) -> f64

    fn respond(query: String) -> String {
        let intent = ai prompt(
            "Classify this query into: time, math, general"
        ) system("You are a classifier")

        match intent {
            "time" => self.get_time()
            "math" => {
                let expr = ai prompt("Extract math expression from: {query}")
                let result = self.calculate(expr)
                "The result is {result}"
            }
            _ => ai prompt(query) model("arcanis-default")
        }
    }
}
