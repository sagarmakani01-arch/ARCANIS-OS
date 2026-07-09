import { ArcanisOS } from "../../index";

export async function main(os: ArcanisOS) {
  const result = await os.executeCommand("echo Hello from ArcanisOS app!");
  console.log(result);
  const thought = await os.brain.think("Welcome to the AI-native future");
  console.log(`[Brain]: ${thought.content}`);
}
