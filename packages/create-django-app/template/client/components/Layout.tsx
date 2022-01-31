import React from "react";
import {Helmet} from "react-helmet-async";
import {css} from "@linaria/core";
import {styled} from "@linaria/react";
import * as styles from "@client/styles";
styles;

import {Context} from "@client/generated";

const Option = styled.a`
    display: grid;
    grid-template-columns: min-content 1fr;
    gap: 10px;
    box-sizing: border-box;
    text-decoration: none;

    & svg {
        width: 1.5rem;
        height: 1.5rem;
        fill: gray;
        border: 1px solid #d6d6d6;
        padding: 5px;
        border-radius: 100%;
    }

    & p {
        font-weight: 300;
        line-height: 1.25;
        color: #525252;
        display: table;
    }
    & .option__heading {
        color: #19865c;
        font-size: 1.25rem;
        font-weight: 400;
    }
`;

const ScreenReader = styled.span`
    clip: rect(1px, 1px, 1px, 1px);
    clip-path: inset(50%);
    height: 1px;
    overflow: hidden;
    position: absolute;
    white-space: nowrap;
    width: 1px;
`;

interface Props {
    title: string;
    children: React.ReactNode;
}

export const Layout = (props: Props) => {
    const context = React.useContext(Context);

    return (
        <>
            <Helmet htmlAttributes={{className: "bar"}}>
                <meta charSet="utf-8" />
                <title>{props.title}</title>
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <link
                    rel="stylesheet"
                    type="text/css"
                    href={`${context.STATIC_URL}admin/css/fonts.css`}
                />
                <link
                    rel="stylesheet"
                    type="text/css"
                    href={`${context.STATIC_URL}dist/index.css`}
                />
                <script defer src={`${context.STATIC_URL}dist/index.js`} />
            </Helmet>
            <header
                className={css`
                    border-bottom: 1px solid #efefef;
                    display: grid;
                    grid-template-columns: auto auto;
                    align-items: self-end;
                    justify-content: space-between;
                    gap: 7px;
                    padding-top: 20px;
                    padding-bottom: 10px;

                    @media (max-width: 800px) {
                        grid-template-columns: 1fr;
                        padding-left: 20px;
                        padding-right: 20px;
                    }
                `}
            >
                <a
                    className={css`
                        font-weight: 700;
                        font-size: 1.375rem;
                        text-decoration: none;
                    `}
                    href="/"
                    rel="noopener"
                >
                    django reactivated
                </a>
                <p>
                    View{" "}
                    <a
                        href={`https://docs.djangoproject.com/en/${context.django_version}/releases/`}
                        target="_blank"
                        rel="noopener"
                    >
                        release notes
                    </a>{" "}
                    for Django {context.django_version}
                </p>
            </header>
            <main
                className={css`
                    text-align: center;

                    & p {
                        line-height: 1.25;
                        max-width: 26rem;
                        margin: 15px auto 0;
                    }

                    & ul {
                        text-align: left;
                        line-height: 1.25;
                        max-width: 26rem;
                        margin: 15px auto 0;
                    }

                    @media (max-width: 800px) {
                        padding: 0 25px;
                        & h1 {
                            font-size: 1.25rem;
                        }
                    }
                `}
            >
                {props.children}
            </main>
            <footer
                className={css`
                    display: grid;
                    grid-template-columns: 1fr 1fr 1fr;
                    gap: 5px;
                    padding: 25px 0;
                    position: fixed;
                    box-sizing: border-box;
                    left: 50%;
                    bottom: 0;
                    width: 960px;
                    transform: translateX(-50%);
                    transform-style: preserve-3d;
                    border-top: 1px solid #efefef;

                    @media (max-width: 996px) {
                        max-width: 780px;
                    }

                    @media (max-width: 800px) {
                        height: 100%;
                        grid-template-columns: 1fr;
                        gap: 60px;
                        position: relative;
                        padding: 25px;
                        width: 100%;
                        margin-top: 50px;
                    }

                    @media (min-width: 801px) and (max-height: 600px) {
                        position: relative;
                        margin: 135px auto 0;
                    }
                `}
            >
                <Option
                    className="option"
                    href={`https://docs.djangoproject.com/en/${context.django_version}/`}
                    target="_blank"
                    rel="noopener"
                >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1zm3-19C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7zm2.85 11.1l-.85.6V16h-4v-2.3l-.85-.6A4.997 4.997 0 017 9c0-2.76 2.24-5 5-5s5 2.24 5 5c0 1.63-.8 3.16-2.15 4.1z" />
                    </svg>
                    <p>
                        <span className="option__heading">Django Documentation</span>
                        <ScreenReader>.</ScreenReader>
                        <br />
                        Topics, references, &amp; how-to’s
                    </p>
                </Option>
                <Option
                    className="option"
                    href={`https://docs.djangoproject.com/en/${context.django_version}/intro/tutorial01/`}
                    target="_blank"
                    rel="noopener"
                >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z" />
                    </svg>
                    <p>
                        <span className="option__heading">Tutorial: A Polling App</span>
                        <ScreenReader>.</ScreenReader>
                        <br />
                        Get started with Django
                    </p>
                </Option>
                <Option
                    className="option"
                    href="https://www.djangoproject.com/community/"
                    target="_blank"
                    rel="noopener"
                >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M16.5 13c-1.2 0-3.07.34-4.5 1-1.43-.67-3.3-1-4.5-1C5.33 13 1 14.08 1 16.25V19h22v-2.75c0-2.17-4.33-3.25-6.5-3.25zm-4 4.5h-10v-1.25c0-.54 2.56-1.75 5-1.75s5 1.21 5 1.75v1.25zm9 0H14v-1.25c0-.46-.2-.86-.52-1.22.88-.3 1.96-.53 3.02-.53 2.44 0 5 1.21 5 1.75v1.25zM7.5 12c1.93 0 3.5-1.57 3.5-3.5S9.43 5 7.5 5 4 6.57 4 8.5 5.57 12 7.5 12zm0-5.5c1.1 0 2 .9 2 2s-.9 2-2 2-2-.9-2-2 .9-2 2-2zm9 5.5c1.93 0 3.5-1.57 3.5-3.5S18.43 5 16.5 5 13 6.57 13 8.5s1.57 3.5 3.5 3.5zm0-5.5c1.1 0 2 .9 2 2s-.9 2-2 2-2-.9-2-2 .9-2 2-2z" />
                    </svg>
                    <p>
                        <span className="option__heading">Django Community</span>
                        <ScreenReader>.</ScreenReader>
                        <br />
                        Connect, get help, or contribute
                    </p>
                </Option>
            </footer>
        </>
    );
};
