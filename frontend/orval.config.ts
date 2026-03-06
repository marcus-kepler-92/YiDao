import { defineConfig } from "orval"

export default defineConfig({
  yidao: {
    input: {
      target: "./openapi.json",
    },
    output: {
      target: "src/api/generated/endpoints.ts",
      schemas: "src/api/generated/models",
      client: "fetch",
      baseUrl: "",
      clean: true,
      prettier: true,
      tsconfig: "tsconfig.app.json",
      override: {
        mutator: {
          path: "src/api/customFetch.ts",
          name: "customFetch",
        },
      },
    },
  },
})
