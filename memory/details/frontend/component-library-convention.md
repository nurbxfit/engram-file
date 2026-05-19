# Frontend Component Library Convention

## Convention

Use **shadcn/ui** as the base component library, customized with our design tokens. Components live in `src/components/ui/`.

## Rules

1. **Never edit shadcn source components directly** — customize via Tailwind CSS variables in `globals.css`.
2. **Compose, don't wrap** — build page-level UIs by composing shadcn primitives, not by creating abstraction layers.
3. **Component exports** — each UI component gets a single barrel export from `src/components/ui/index.ts`.
4. **Variants** — use `cva` (Class Variance Authority) for component variants, not prop-based conditionals.
5. **Forms** — use `react-hook-form` with `zod` schemas for all form validation; shadcn `Form` component as the UI layer.

## File Structure

```
src/components/
├── ui/          ← shadcn components (untouched)
│   ├── button.tsx
│   ├── input.tsx
│   └── ...
├── forms/       ← form wrappers using react-hook-form + shadcn
└── layout/      ← app layout components
```

## Status

Active. Established at project start.
