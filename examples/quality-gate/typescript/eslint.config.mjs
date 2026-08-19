// Merge this rule block into the target's existing ESLint flat configuration.
export default [
  {
    rules: {
      complexity: ["error", 10],
      "no-warning-comments": ["warn", { terms: ["TODO", "FIXME"], location: "anywhere" }]
    }
  }
]
