import {style, globalStyle} from "@vanilla-extract/css";

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
})

globalStyle("html", {
      lineHeight: 1.15,
      height: '100%',
})
globalStyle("body", {
    color: '#2e3440',
      fontFamily: '-apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      height: '100%',
      margin: 0,
      fontSize: '15px',
})


globalStyle("a", {
    color: '#189ab4',
})

globalStyle("h1, h2, h3, h4, h5, h6, p, ul", {
     padding: 0,
      margin: 0,
      fontWeight: 400,
      listStyleType: 'none',
})

globalStyle("h1, h2, h3, h4, h5, h6", {
      color: colors.header,
      fontFamily: "'Suez One', serif",
})

globalStyle("hr", {
 borderColor: colors.header,
      borderWidth: 0.5,
      borderStyle: 'solid',
      margin: 0,
})

globalStyle('input[type="text"]', {
      font: 'inherit',
      padding: '10px',
      border: '1px solid #ccc',
      width: '100%',
})

globalStyle("pre", {
 margin: '0 !important',
      padding: 0,
      borderRadius: '15px',
})

globalStyle("#root", {
     display: 'flex',
      flexDirection: 'column',
      height: '100%',
})


export const hideOnMobile = style({
    "@media": {
        [$mobile]: {
            display: "none !important",
        },
    },


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
})

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

})

export const homePageButtons = style({
                                display: "flex",
                                gap: 15,


    "@media": {
        [$mobile]: {
            justifyContent: "center",
        },
    },

})


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
})

globalStyle(`${homePageFeatures} > *`, {
                                    width: "100%",
                                    display: "flex",
                                    flexDirection: "column",
                                    gap: 10,
})

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
})

globalStyle(`${homePageLinks} > *`, {
                                    width: "100%",
                                    display: "flex",
                                    flexDirection: "column",
                                    gap: 10,
                                    textAlign: "center",
})
