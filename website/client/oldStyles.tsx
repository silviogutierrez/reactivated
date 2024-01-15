import {css} from "@linaria/core";

import * as CSS from "csstype";

import "@client/fonts.css";

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
