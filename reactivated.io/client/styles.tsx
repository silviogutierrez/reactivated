import {css} from "@linaria/core";

import * as CSS from "csstype";

type Styles = CSS.Properties<string | number> & {
    $mobile?: CSS.Properties<string | number>;
    $desktop?: CSS.Properties<string | number>;
    $nest?: {[name: string]: CSS.Properties<string | number>};
};

export function style(...objects: Styles[]) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let merged: Record<string, any> = {};

    for (const arg of objects) {
        const {$nest, $mobile, $desktop, ...styleProp} = arg;
        merged = Object.assign({}, merged, styleProp, $nest);

        if ($mobile) {
            merged["@media (max-width: 1200px)"] = $mobile;
        }
        if ($desktop) {
            merged["@media (min-width: 1201px)"] = $desktop;
        }
    }
    return merged;
}

export const globalStyles = () => css`
    :global() {
        *,
        *::before,
        *::after {
            box-sizing: border-box;
        }

        html {
            line-height: 1.15;
            height: 100%;
        }

        a {
            color: #189ab4;
        }
        body {
            color: #2e3440;
            font-family: -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI",
                Roboto, "Helvetica Neue", Arial, sans-serif;
            height: 100%;
            margin: 0;
            font-size: 15px;
        }

        h1,
        h2,
        h3,
        h4,
        h5,
        h6 {
            ${style({
                color: colors.header,
                fontFamily: "'Suez One', serif",
            })}
        }

        hr {
            ${style({
                borderColor: colors.header,
                borderWidth: 0.5,
                borderStyle: "solid",
                margin: 0,
            })}
        }

        h1,
        h2,
        h3,
        h4,
        h5,
        p,
        ul {
            padding: 0;
            margin: 0;
            font-weight: 400;
            list-style-type: none;
        }

        code {
        }

        input[type="text"] {
            font: inherit;
            padding: 10px;
            border: 1px solid #ccc;
            width: 100%;
        }

        pre {
            margin: 0 !important;
            padding: 0;
            border-radius: 15px;
        }

        #root {
            ${style({
                display: "flex",
                flexDirection: "column",
                height: "100%",
            })}
        }
    }
`;

// https://www.canva.com/colors/color-palettes/summer-splash/
export const colors = {
    background: "#D4F1F4",
    darkBackground: "#c7e7eb",
    header: "#05445E",
    textWithColor: "#127387",
    warningBorder: "#EDBC9B",
    warningBackground: "#fdf6f2",
    warningText: "#b15a20",
    warningDarkBackground: "#f8e5d8",
};
