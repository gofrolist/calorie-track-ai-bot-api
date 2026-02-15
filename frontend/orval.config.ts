import { defineConfig } from 'orval';

export default defineConfig({
  api: {
    input: {
      target: './openapi.json',
      validation: false,
    },
    output: {
      target: './src/api/queries',
      schemas: './src/api/model',
      client: 'react-query',
      mode: 'tags-split',
      clean: true,
      override: {
        mutator: {
          path: './src/api/client.ts',
          name: 'customFetch',
        },
        query: {
          useQuery: true,
          useMutation: true,
          signal: true,
        },
      },
    },
  },
});
