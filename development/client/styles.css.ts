import {globalStyle, style, keyframes} from "@vanilla-extract/css";
import {createSprinkles, defineProperties} from "@vanilla-extract/sprinkles";

const layout = defineProperties({
    properties: {
        display: ["none", "flex", "block", "inline"],
        flexDirection: ["row", "column"],
        gap: [5, 10],
    },
});

const typography = defineProperties({
    properties: {
        fontWeight: [700],
        color: ["#cf0000"],
    },
});

export const sprinkles = createSprinkles(layout, typography);

export const Fieldset = style({
    border: "1px solid #bbb",
    borderRadius: 5,
    padding: 20,
});

export const Button = style({
    border: "1px solid #bbb",
    borderRadius: 5,
    padding: "10px 15px",
    font: "inherit",
    textTransform: "lowercase",
    fontWeight: 700,
    backgroundColor: "white",
    color: "#444",
    cursor: "pointer",
});

export const ButtonLink = style({
    display: "inline-block",
    border: "1px solid #bbb",
    borderRadius: 5,
    padding: "10px 15px",
    font: "inherit",
    textTransform: "lowercase",
    fontWeight: 700,
    backgroundColor: "white",
    color: "#444",
    cursor: "pointer",
    textDecoration: "none",
});

export const djangoDefaultMain = style({
    textAlign: "center",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    "@media": {
        "(max-width: 800px)": {
            padding: "0 25px",
        },
    },
});

globalStyle(`${djangoDefaultMain} p`, {
    lineHeight: "1.25",
    maxWidth: "26rem",
});

globalStyle(`${djangoDefaultMain} ul`, {
    textAlign: "left",
    lineHeight: "1.25",
    maxWidth: "26rem",
});

globalStyle(`${djangoDefaultMain} h1`, {
    fontSize: "1.375rem",
    maxWidth: "32rem",

    "@media": {
        "(max-width: 800px)": {
            fontSize: "1.25rem",
        },
    },
});

export const djangoDefaultMainSvg = style({
    marginTop: "19vh",
    maxWidth: 265,
    position: "relative",
    zIndex: -9,
    overflow: "visible",

    "@media": {
        "(max-width: 800px)": {
            marginTop: 10,
        },

        "(min-width: 801px) and (max-height: 730px)": {
            marginTop: 80,
        },

        "(min-width: 801px) and (max-height: 600px)": {
            marginTop: 50,
        },
    },
});

const smokeAnimation = keyframes({
    "0%": {
        transform: "translate3d(-5px, 0, 0)",
    },
    "100%": {
        transform: "translate3d(5px, 0, 0)",
    },
});

export const smokePath = style({
    animation: `${smokeAnimation} 0.1s 70 ease-in-out alternate`,

    "@media": {
        "(prefers-reduced-motion: reduce)": {
            animation: "none",
        },
    },
});

export const thrustAnimation = keyframes({
    "0%": {
        opacity: 0,
    },
    "100%": {
        opacity: 0.5,
    },
});


export const thrustPath = style({
    animation: `${thrustAnimation} 70ms 100 ease-in-out alternate`,

    "@media": {
        "(prefers-reduced-motion: reduce)": {
            animation: "none",
        },
    },
});

export const burnAnimation = keyframes({
    "0%": {
        transform: "translate3d(0, 0, 0)",
    },
    "100%": {
        transform: "translate3d(0, 3px, 0)",
    },
});

export const burnPath = style({
    animation: `${burnAnimation} 0.1s 70 ease-in-out alternate`,

    "@media": {
        "(prefers-reduced-motion: reduce)": {
            animation: "none",
        },
    },
});

globalStyle("*, *::before, *::after", {
    boxSizing: 'border-box',
});


globalStyle("html", {
    lineHeight: 1.15,
});

globalStyle("a", {
    color: '#19865c',
});

globalStyle("body", {
    maxWidth: '960px',
    color: '#525252',
    fontFamily: 'Roboto, sans-serif',
    margin: '0 auto',
    "@media": {
      '(max-width: 996px)': {
          maxWidth: '780px',
      },
    },
});

globalStyle("h1, h2, h3, h4, h5, h6", {
    padding: 0,
    margin: 0,
    fontWeight: 400,
    listStyleType: 'none',
});

globalStyle("h1", {
    fontSize: '1.375rem',
});

globalStyle('input[type="text"]', {
    font: 'inherit',
    padding: '10px',
    border: '1px solid #ccc',
    width: '100%',
});
