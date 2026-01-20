# AGENTS.md

This file provides context and instructions for AI agents operating in this repository.

## 1. Build, Lint, and Test Commands

### Package Management

- This project uses **pnpm**. Always use `pnpm` instead of `npm` or `yarn`.
- Install dependencies: `pnpm install`

### Scripts (from `package.json`)

- **Development Server**: `pnpm dev`
- **Build**: `pnpm build` (Uses Vite)
- **Preview Build**: `pnpm preview`
- **Lint**: `pnpm lint` (Runs Prettier check and ESLint)
- **Format**: `pnpm format` (Runs Prettier write)
- **Type Check**: `pnpm check` (Runs `svelte-check` against `tsconfig.json`)
- **Watch Type Check**: `pnpm check:watch`

### Testing

- **Status**: There are currently no test scripts defined in `package.json` and no visible test files in `src`.
- **Instruction**: If adding tests, use **Vitest** (compatible with Vite).
- **Running Tests**: Since no test script exists, if you create tests, add a script `"test": "vitest"` to `package.json`.
- **Single Test**: To run a single test file (once configured): `npx vitest run path/to/file.test.ts`

## 2. Code Style & Conventions

### Tech Stack

- **Framework**: SvelteKit (Svelte 5)
- **Language**: TypeScript (`.ts`, `.svelte`)
- **Styling**: Tailwind CSS (configured via Vite plugin)
- **Bundler**: Vite

### Formatting & Linting

- **Prettier**: Strictly enforced. Run `pnpm format` after changes.
- **ESLint**: configured in `eslint.config.js`. Includes:
  - `js.configs.recommended`
  - `ts.configs.recommended`
  - `svelte.configs.recommended`
  - `prettier` integration

### File Structure

- `src/routes/`: SvelteKit routes (file-based routing).
  - `+page.svelte`: Page component.
  - `+layout.svelte`: Layout component.
  - `+server.ts`: API endpoints.
- `src/lib/`: Shared utilities and components.
  - `$lib` alias is configured.
- `src/components/`: Reusable Svelte components (e.g., `Card.svelte`, `Navigation.svelte`).

### Svelte Conventions

- Use the `<script lang="ts">` block for TypeScript.
- Use Svelte 5 runes (`$state`, `$props`) where appropriate (project uses Svelte 5).
- **Props**: Use the `$props()` rune for defining component props.
  ```svelte
  <script lang="ts">
  	let { myProp = 'default' }: { myProp?: string } = $props();
  </script>
  ```
- **State**: Use `$state()` for reactive variables.
  ```svelte
  <script lang="ts">
  	let count = $state(0);
  </script>
  ```

### Naming Conventions

- **Files**:
  - Svelte components: `PascalCase.svelte` (e.g., `Card.svelte`).
  - SvelteKit routes: `+page.svelte`, `+layout.svelte`.
  - TypeScript files: `camelCase.ts` or `kebab-case.ts`.
- **CSS Variables**: `kebab-case` (e.g., `--glass-bg`).

### CSS & Tailwind

- Use Tailwind utility classes for layout and spacing.
- Use CSS variables for theme colors and glassmorphism effects (defined in `src/routes/+layout.svelte` or `src/routes/layout.css`).
- **Glassmorphism**: Use the project's standard variables (`--glass-bg`, `--glass-border`, etc.) to maintain consistency.

### Imports

- Use the `$lib` alias for importing from `src/lib`.
- **DO NOT** use relative paths like `../../lib` if `$lib` can be used.
- Import standard Svelte functions (like `onMount`) from `svelte`.

### Error Handling

- Use SvelteKit's `error` helper for route errors.
  ```ts
  import { error } from '@sveltejs/kit';
  throw error(404, 'Not found');
  ```

## 3. Cursor / Copilot Rules

_No specific .cursorrules or .github/copilot-instructions.md found._

## 4. Agent Behavior Guidelines

- **Plan First**: Always analyze the file structure and existing conventions before editing.
- **Read-Only**: Use `read` to inspect files. Do not assume file contents.
- **Minimal Changes**: Only modify what is requested.
- **Safety**: Do not commit secrets.
- **Verification**: Run `pnpm check` and `pnpm lint` after making significant changes to ensure type safety and code style compliance.
