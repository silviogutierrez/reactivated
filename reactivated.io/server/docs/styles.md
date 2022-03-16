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

Classic CSS is fine, but it's not great. But we believe firmly the best approach is
CSS-in-JS that statically compiles to a CSS stylesheet. Currently, there are two
dominant players in the field, and both require special tooling.

So Reactivated supports them _both_. For now.

Both will automatically produce styles into your `index.css` asset. You can even mix and
match them to see what works best.

### Linaria

The first option is [Linaria](https://linaria.dev). The best way to describe it is
[styled-components](https://styled-components.com) but statically compiled.

Just import `css` from `@linaria/core` and create class names you can attach to your
components. You can use the `cx` helper for conditional application of classes.

Imagine our component `@client/components/Banner.tsx`:

```typescript
import React from "react";

import {css, cx} from "@linaria/core";

const banner = css`
    background: red;
    border: 1px solid black;
`;

const highlighted = css`
    bordercolor: blue;
`;

export const Banner = (props: {
    children: React.React.Node;
    isHighlighted?: boolean;
}) => (
    <div className={cx(banner, props.isHighlighted === true && highlighted)}>
        {props.children}
    </div>
);
```

This is just one example. Linaria has a
[powerful API](https://github.com/callstack/linaria#syntax) with many more features,
including styles based on `props` and a shorthand to create components.

### Vanilla Extract

[Vanilla Extract](https://vanilla-extract.style) is the newer library in the space. It's
similar to Linaria but has a few key difference. Some make it better, some worse.

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

// Vanilla Extract does not currently bundle an equivalent utility.
// There's probably a more idiomatic way to do this conditionally using
// styleVariants though.
import {cx} from "@linaria/core";

import * as css from "./Banner.css"

export const Banner = (props: {
    children: React.React.Node;
    isHighlighted?: boolean;
}) => (
    <div className={cx(css.banner, props.isHighlighted === true && css.highlighted)}>
        {props.children}
    </div>
);
```

You can see Vanilla Extract encourages type safety and pure TypeScript usage.
Like Linaria, it has a powerful — possibly better documented — [API](https://vanilla-extract.style/documentation).

## Next steps

Be sure to read our [request for comments](/documentation/rfc/) to provide feedback
on these two libraries and help us choose the One True Way™.

## Other tools

You can likely use JS-only CSS-in-JS libraries like [emotion](https://emotion.sh/) and
[styled-components](https://styled-components.com).

So long as you stick their runtime-only, no-tooling offerings.
