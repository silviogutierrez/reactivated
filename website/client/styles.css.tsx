import {globalStyle, style} from "@vanilla-extract/css";

const $mobile = "(max-width: 1200px)";
const $desktop = "(min-width: 1201px)";

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

globalStyle("*, *::before, *::after", {
    boxSizing: "border-box",
});

globalStyle("html", {
    lineHeight: 1.15,
    height: "100%",
});
globalStyle("body", {
    color: "#2e3440",
    fontFamily:
        '-apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    height: "100%",
    margin: 0,
    fontSize: "15px",
});

globalStyle("a", {
    color: "#189ab4",
});

globalStyle("h1, h2, h3, h4, h5, h6, p, ul", {
    padding: 0,
    margin: 0,
    fontWeight: 400,
    listStyleType: "none",
});

globalStyle("h1, h2, h3, h4, h5, h6", {
    color: colors.header,
    fontFamily: "'Suez One', serif",
});

globalStyle("hr", {
    borderColor: colors.header,
    borderWidth: 0.5,
    borderStyle: "solid",
    margin: 0,
});

globalStyle('input[type="text"]', {
    font: "inherit",
    padding: "10px",
    border: "1px solid #ccc",
    width: "100%",
});

globalStyle("pre", {
    margin: "0 !important",
    padding: 0,
    borderRadius: "15px",
});

globalStyle("#root", {
    display: "flex",
    flexDirection: "column",
    height: "100%",
});

export const hideOnMobile = style({
    "@media": {
        [$mobile]: {
            display: "none !important",
        },
    },
});

export const Fieldset = style({
    border: "1px solid #bbb",
    borderRadius: 5,
    padding: 20,
});

export const Button = style({
    borderWidth: 2,
    borderStyle: "solid",
    borderColor: colors.header,
    borderRadius: "5px",
    backgroundColor: colors.header,
    padding: "10px 15px",
    font: "inherit",
    textTransform: "lowercase",
    fontWeight: 700,
    cursor: "pointer",
    textDecoration: "none",
    color: "white",
    display: "flex",
    alignItems: "center",
});

export const Highlight = style({
    display: "flex",
    gap: 15,

    paddingLeft: 50,
    paddingRight: 50,
    "@media": {
        [$mobile]: {
            flexDirection: "column",
            paddingLeft: 0,
            paddingRight: 0,
        },
    },
});

globalStyle(`${Highlight} p`, {
    fontSize: 17,
});

globalStyle(`${Highlight} > *`, {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    gap: 15,
    justifyContent: "center",
    textAlign: "center",
});

export const InstallationCommand = style({
    margin: 0,
    padding: 15,
    fontSize: 14,
    fontFamily: "Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace",
    backgroundColor: colors.darkBackground,
    inlineSize: "min-content",
    borderRadius: "10px",
    color: colors.header,
    lineHeight: 1.5,

    overflow: "hidden",
    maxWidth: "100%",
    textOverflow: "ellipsis",
});

export const Links = style({
    display: "flex",
    flexDirection: "column",
    gap: 5,
});

export const homePageHeader = style({
    maxWidth: 1200,
    margin: "0 auto",

    paddingLeft: 20,
    paddingRight: 20,

    paddingTop: 100,
    paddingBottom: 75,

    display: "flex",
    gap: 30,

    "@media": {
        [$mobile]: {
            flexDirection: "column",
            paddingTop: 20,
            paddingBottom: 20,
        },
    },
});

export const homePageButtons = style({
    display: "flex",
    gap: 15,

    "@media": {
        [$mobile]: {
            justifyContent: "center",
        },
    },
});

export const homePageFeatures = style({
    display: "flex",
    paddingLeft: 40,
    paddingRight: 40,

    gap: 30,

    "@media": {
        [$mobile]: {
            flexDirection: "column",
            padding: 0,
        },
    },
});

globalStyle(`${homePageFeatures} > *`, {
    width: "100%",
    display: "flex",
    flexDirection: "column",
    gap: 10,
});

export const homePageLinks = style({
    paddingLeft: 50,
    paddingRight: 50,
    display: "flex",

    "@media": {
        [$mobile]: {
            flexDirection: "column",
            gap: 15,
        },
    },
});

globalStyle(`${homePageLinks} > *`, {
    width: "100%",
    display: "flex",
    flexDirection: "column",
    gap: 10,
    textAlign: "center",
});

export const Hamburger = style({
    background: "white",
    borderRadius: "50%",
    width: 40,
    height: 40,
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    border: 0,
    cursor: "pointer",
    boxShadow: "0 4px 8px rgb(14 14 33 / 20%)",

    "@media": {
        [$desktop]: {
            display: "none !important",
        },
    },
});

export const Menu = style({
    width: 300,
    backgroundColor: colors.background,
    paddingTop: 30,
    paddingBottom: 30,
    paddingLeft: 10,
    paddingRight: 10,
    position: "relative",

    "@media": {
        [$mobile]: {
            padding: 15,
            display: "flex",
            width: "auto",
        },
    },
});

export const documentationLayout = style({
    display: "flex",
    flex: 1,

    "@media": {
        [$mobile]: {
            flexDirection: "column",
        },
    },
});

export const Documentation = style({
    display: "flex",
    flexDirection: "column",
    gap: 15,
    flex: 1,
    maxWidth: 800,
    margin: "0 auto",
    paddingLeft: 20,
    paddingRight: 20,
    "@media": {
        [$mobile]: {
            maxWidth: "100%",
        },
    },
});

globalStyle(`${Documentation} blockquote`, {
    borderLeft: 5,
    borderLeftStyle: "solid",
    borderLeftColor: colors.textWithColor,
    margin: 0,
    padding: "15px 20px",
});

globalStyle(`${Documentation} ul`, {
    listStyleType: "disc",
    marginLeft: 20,
    lineHeight: "22px",
});

globalStyle(`${Documentation} p`, {
    lineHeight: "22px",
});

export const ReactMarkdown = style({
    display: "flex",
    flexDirection: "column",
    position: "sticky",
    top: 30,
    gap: 10,
});

globalStyle(`${ReactMarkdown} a`, {
    textDecoration: "none",
});
globalStyle(`${ReactMarkdown} h2 a`, {
    color: colors.header,
});
globalStyle(`${ReactMarkdown} h2`, {
    color: colors.header,
    fontSize: 18,
});
globalStyle(`${ReactMarkdown} h3 a`, {
    color: colors.textWithColor,
});
globalStyle(`${ReactMarkdown} h3`, {
    fontFamily: "inherit",
    fontSize: 16,
    color: colors.textWithColor,
});

export const warning = style({
    borderColor: `${colors.warningBorder} !important`,
    backgroundColor: colors.warningBackground,
});

export const inlineCode = style({
    fontFamily: "Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace",
    padding: "1px 3px",
    fontSize: 14,
    borderRadius: 5,
    backgroundColor: colors.background,
    color: colors.textWithColor,
});

globalStyle(`${warning} ${inlineCode}`, {
    color: colors.warningText,
    backgroundColor: colors.warningDarkBackground,
});

export const menu = style({
    display: "flex",
    flexDirection: "column",
    flex: 1,
    gap: 20,
    marginLeft: 20,
    fontSize: 17,
    "@media": {
        [$mobile]: {
            marginLeft: -10,
            alignItems: "center",
            gap: 10,
        },
    },
});

globalStyle(`h3 ${inlineCode}`, {
    fontSize: 18,
});

globalStyle(`${warning} a`, {
    color: colors.warningText,
});

globalStyle(`#menu:not(:checked) ~ ${menu}`, {
    "@media": {
        [$mobile]: {
            display: "none !important",
        },
    },
});
