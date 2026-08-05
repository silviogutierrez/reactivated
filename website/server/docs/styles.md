# Styling your application

Without any configuration, you can write CSS files and import them from your components.
No magic, no tooling.

The simplest approach would be to import your stylesheet in your layout component.
Imagine our templates all render inside `BASE_DIR/client/components/Layout.tsx`:

```typescript
import React from "react";

import "@client/styles.css";

export const Layout = (props: {children: React.ReactNode}) => (
    <div className="layout">{props.children}</div>
);
```

And inside `client/styles.css` write our styles:

```css
.layout {
    width: 800px;
    margin: 0 auto;
}
```

No magic, no tooling. Just classic CSS.

## Tailwind, built in

Classic CSS is fine, but most projects reach for [Tailwind](https://tailwindcss.com)
these days, and we get the appeal: utilities colocate with the markup, and colocation
is [kind of our thing](/documentation/philosophy-goals/#colocation-is-a-good-thing).

So Reactivated ships it. Tailwind 4 runs inside the dev server and the production
build automatically. There's no `tailwind.config.js`, no PostCSS setup, no plugin to
wire. Start your stylesheet with the import and you're done:

```css
@import "tailwindcss";
```

That's the entire setup. Utilities now work in any component:

```typescript
export const Card = (props: {children: React.ReactNode}) => (
    <div className="rounded border p-4 shadow">{props.children}</div>
);
```

Tailwind 4 is configured in CSS, not JavaScript. Design tokens go in a `@theme`
block in the same file:

```css
@import "tailwindcss";

@theme {
    --color-brand: #1c1917;
    --font-sans: "Inter", sans-serif;
}
```

And every token mints its utilities: `bg-brand`, `text-brand`, `font-sans`, and so
on.

For conditional classes, `classNames` from `@reactivated` keeps the markup tidy:

```typescript
import {classNames} from "@reactivated";

export const Banner = (props: {
    children: React.ReactNode;
    isHighlighted?: boolean;
}) => (
    <div
        className={classNames(
            "rounded border p-4",
            props.isHighlighted === true && "bg-brand text-white",
        )}
    >
        {props.children}
    </div>
);
```

> **Note**: Import your stylesheet from a component like `Layout`, or from
> `client/index.tsx` if you [have one](/documentation/templates/#the-entry-point).
> Either way it flows through Vite, so Tailwind processes it in dev and in the
> production build alike.

## Other tools

You can likely use JS-only CSS-in-JS libraries like [emotion](https://emotion.sh/) and
[styled-components](https://styled-components.com).

So long as you stick to their runtime-only, no-tooling offerings.

## Next steps

Be sure to read our [request for comments](/documentation/rfc/) to provide feedback.
