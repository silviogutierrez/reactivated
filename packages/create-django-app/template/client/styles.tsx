import {css} from "@linaria/core";

css`
    :global() {
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
        }
        h1 {
            font-size: 1.375rem;
            max-width: 32rem;
            margin: 5px auto 0;
        }
        @media (max-width: 996px) {
            body {
                max-width: 780px;
            }
        }
    }
`;

export const verticallySpaced = css`
    & > * {
        margin-bottom: 10px;
    }
    & > *:last-child {
        margin-bottom: 0 !important;
    }
`;

export const horizontallySpaced = css`
    & > * {
        margin-right: 10px;
    }
    & > *:last-child {
        margin-right: 0 !important;
    }
`;
