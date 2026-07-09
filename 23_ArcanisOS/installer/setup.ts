import { ArcanisInstaller } from "./index";

async function main() {
  const installer = new ArcanisInstaller(__dirname, {
    prefix: process.env.ARCANIS_PREFIX || "C:\\ArcanisOS",
    components: ["kernel", "ai", "interface", "development", "security", "integration"],
    withExamples: true,
    withDocs: true,
  });

  console.log("ArcanisOS Installer v1.0.0-alpha");
  console.log("=".repeat(40));

  try {
    const result = await installer.install();
    console.log(`\n✓ Installation complete`);
    console.log(`  Path: ${result.path}`);
    console.log(`  Components: ${result.components.join(", ")}`);

    const verify = await installer.verify();
    if (verify.complete) {
      console.log("\n✓ All components verified successfully");
    } else {
      console.log(`\n⚠ Missing components: ${verify.missing.join(", ")}`);
    }
  } catch (error) {
    console.error("\n✗ Installation failed:", error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}
