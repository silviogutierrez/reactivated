import {css} from "@linaria/core";

export const globalStyles = css`
    :global() {
        *,
        *::before,
        *::after {
            box-sizing: border-box;
        }

        html {
            line-height: 1.15;
        }

        a {
            color: #19865c;
        }
        body {
            max-width: 960px;
            color: #525252;
            font-family: Roboto, sans-serif;
            margin: 0 auto;
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
        h1 {
            font-size: 1.375rem;
        }
        @media (max-width: 996px) {
            body {
                max-width: 780px;
            }
        }

        input[type="text"] {
            font: inherit;
            padding: 10px;
            bordeer: 1px solid #ccc;
            width: 100%;
        }
    }
`;

export const verticallySpaced = (space: 5 | 10) => ({
    "& > *": {
        marginBottom: space,
    },
    "& > *:last-child": {
        marginBottom: "0 !important",
    },
});

export const horizontallySpaced = css`
    & > * {
        margin-right: 10px;
    }
    & > *:last-child {
        margin-right: 0 !important;
    }
`;
