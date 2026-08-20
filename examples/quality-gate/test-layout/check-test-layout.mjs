import { execFileSync } from "node:child_process";

// Example for repositories that keep TypeScript/JavaScript production code in
// `src/` and unit tests in a module-level `tests/` directory. Adapt the root
// prefixes and exceptions to the target repository; do not claim a generic
// layout rule covers frameworks with different discovery conventions.
const TEST_IN_SOURCE =
  /^(?:frontend|gateway)\/.+\/src\/.+\.(?:test|spec)\.(?:[cm]?[jt]sx?)$/;

function candidatePaths() {
  const supplied = process.argv
    .slice(2)
    .filter((argument) => !argument.startsWith("-"));
  if (supplied.length > 0) return supplied;

  return execFileSync(
    "git",
    ["ls-files", "--cached", "--others", "--exclude-standard"],
    { encoding: "utf8" },
  )
    .split(/\r?\n/u)
    .filter(Boolean);
}

const violations = candidatePaths()
  .map((path) => path.replaceAll("\\", "/"))
  .filter((path) => TEST_IN_SOURCE.test(path));

if (violations.length > 0) {
  console.error(
    "Tests must live in a module-level tests/ directory, not under src/:",
  );
  for (const path of violations) console.error(`- ${path}`);
  process.exit(1);
}

console.log("Test layout check passed.");
