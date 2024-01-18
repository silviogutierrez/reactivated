# Styling your application

Without any configuration, you can write CSS files and import them from your components.
No magic, no tooling.

The simplest approach would be to import your stylesheet in your layout component.
Imagine our templates all render inside `BASE_DIR/components/Layout.tsx`:

```typescript
import React from "react";

import "@client/styles.css";

export const Layout = (props: {children: React.ReactNode}) => (
    <div className="layout">{props.children}</div>
);
```

And inside `BASE_DIR/style.css` write our styles:

```css
.layout {
    width: 800px;
    margin: 0 auto;
}
```

No magic, no tooling. Just classic CSS.

## Zero runtime CSS-in-JS

Classic CSS is fine, but it's not great. But we firmly believe the best approach is
CSS-in-JS that statically compiles to a CSS stylesheet.

[Vanilla Extract](https://vanilla-extract.style) is one of the newer libraries in the
space. Reactivated comes with built-in support. No extra tooling or configuration
needed.

**There is no [colocation](https://kentcdodds.com/blog/colocation)** with Vanilla
Extract. Styles _need_ to be in a separate file. Still written in TypeScript though.

Our simple example would have `@client/components/Banner.css.ts`:

```typescript
import {style} from "@vanilla-extract/css";

export const banner = style({
    background: "red",
    border: "1px solid black",
});

export const highlighted = style({
    backgroundColor: "blue",
});
```

And our `@client/components/Banner.tsx`:

```typescript
import React from "react";

import {classNames} from "@reactivated";

import * as css from "./Banner.css";

export const Banner = (props: {
    children: React.React.Node;
    isHighlighted?: boolean;
}) => (
    <div
        className={classNames(
            css.banner,
            props.isHighlighted === true && css.highlighted,
        )}
    >
        {props.children}
    </div>
);
```

You can see Vanilla Extract encourages type safety and pure TypeScript usage. It has a
powerful [API](https://vanilla-extract.style/documentation).

## Next steps

Be sure to read our [request for comments](/documentation/rfc/) to provide feedback.

## Other tools

You can likely use JS-only CSS-in-JS libraries like [emotion](https://emotion.sh/) and
[styled-components](https://styled-components.com).

So long as you stick their runtime-only, no-tooling offerings.
