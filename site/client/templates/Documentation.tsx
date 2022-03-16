import React from "react";

import {templates} from "@reactivated";
import {Helmet} from "react-helmet-async";
import ReactMarkdown from "react-markdown";

import {css, cx} from "@linaria/core";

import {Code} from "@client/components/Code";
import {Layout} from "@client/components/Layout";
import * as styles from "@client/styles";

const warning = css`
    ${styles.style({
        borderColor: `${styles.colors.warningBorder} !important`,
        backgroundColor: styles.colors.warningBackground,
    })}
`;

const inlineCode = css`
    ${styles.style({
        fontFamily: "Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace",
        padding: "1px 3px",
        fontSize: 14,
        borderRadius: 5,
        backgroundColor: styles.colors.background,
        color: styles.colors.textWithColor,
    })}

    .${warning} & {
        ${styles.style({
            color: styles.colors.warningText,
            backgroundColor: styles.colors.warningDarkBackground,
        })}
    }
`;

css`
    :global() {
        h3 .${inlineCode} {
            ${styles.style({
                fontSize: 18,
            })};
        }

        .${warning} a {
            ${styles.style({
                color: styles.colors.warningText,
            })}
        }
    }
`;

const menu = css`
    ${styles.style({
        $mobile: {
            display: "none !important",
        },
    })}
`;

export const Hamburger = (props: {onClick: () => void}) => {
    return (
        <button
            className={cx(
                css`
                    ${styles.style({
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
                    })}
                `,
                css`
                    ${styles.style({
                        $desktop: {
                            display: "none !important",
                        },
                    })}
                `,
            )}
            onClick={props.onClick}
        >
            <svg
                xmlns="http://www.w3.org/2000/svg"
                width="2em"
                height="2em"
                viewBox="0 0 20 20"
            >
                <path d="M17.5 6h-15a.5.5 0 010-1h15a.5.5 0 010 1zM17.5 11h-15a.5.5 0 010-1h15a.5.5 0 010 1zM17.5 16h-15a.5.5 0 010-1h15a.5.5 0 010 1z" />
            </svg>
        </button>
    );
};

const Menu = (props: templates.Documentation) => {
    const [isOpen, setIsOpen] = React.useState(false);

    return (
        <aside
            className={css`
                ${styles.style({
                    width: 300,
                    backgroundColor: styles.colors.background,
                    paddingTop: 30,
                    paddingBottom: 30,
                    paddingLeft: 10,
                    paddingRight: 10,
                    position: "relative",

                    $mobile: {
                        padding: 15,
                        display: "flex",
                        width: "auto",
                    },
                })}
            `}
        >
            <Hamburger onClick={() => setIsOpen(!isOpen)} />
            <ul
                className={cx(
                    css`
                        ${styles.style({
                            display: "flex",
                            flexDirection: "column",
                            flex: 1,
                            gap: 20,
                            marginLeft: 20,
                            fontSize: 17,
                            $mobile: {
                                alignItems: "center",
                                gap: 10,
                            },
                        })}
                    `,
                    isOpen === false && menu,
                )}
            >
                <li>
                    <h1>
                        <a
                            href="/"
                            className={css`
                                ${styles.style({
                                    color: styles.colors.header,
                                    textDecoration: "none",
                                })}
                            `}
                        >
                            Reactivated
                        </a>
                    </h1>
                </li>
                {props.toc.map(([link, title]) => {
                    const href = `/documentation/${link}/`;

                    return (
                        <li
                            key={link}
                            className={cx(
                                css`
                                    ${styles.style({
                                        paddingLeft: 8,
                                        borderColor: styles.colors.background,
                                        borderLeftWidth: 3,
                                        borderLeftStyle: "solid",
                                    })}
                                `,
                                href == props.path &&
                                    css`
                                        ${styles.style({
                                            borderColor: styles.colors.textWithColor,
                                        })}
                                    `,
                            )}
                        >
                            <a
                                className={css`
                                    ${styles.style({color: styles.colors.header})}
                                `}
                                href={href}
                            >
                                {title}
                            </a>
                        </li>
                    );
                })}
            </ul>
        </aside>
    );
};

export default (props: templates.Documentation) => (
    <Layout title={null}>
        <div
            className={css`
                ${styles.style({
                    display: "flex",
                    flex: 1,

                    $mobile: {
                        flexDirection: "column",
                    },
                })}
            `}
        >
            <Menu {...props} />
            <div
                className={css`
                    ${styles.style({
                        display: "flex",
                        flexDirection: "column",
                        gap: 15,
                        flex: 1,
                        maxWidth: 800,
                        margin: "0 auto",
                        paddingLeft: 20,
                        paddingRight: 20,
                        $mobile: {
                            maxWidth: "100%",
                        },
                        paddingTop: 30,
                        paddingBottom: 30,
                        $nest: {
                            "& blockquote": {
                                borderLeft: 5,
                                borderLeftStyle: "solid",
                                borderLeftColor: styles.colors.textWithColor,
                                margin: 0,
                                padding: "15px 20px",
                            },
                            "& ul": {
                                listStyleType: "disc",
                                marginLeft: 20,
                                lineHeight: "22px",
                            },
                            "& p": {
                                lineHeight: "22px",
                            },
                        },
                    })}
                `}
            >
                <ReactMarkdown
                    components={{
                        h1: ({children}) => {
                            return (
                                <>
                                    <Helmet>
                                        <title>{children[0]} | Reactivated</title>
                                    </Helmet>
                                    <h1>{children}</h1>
                                </>
                            );
                        },
                        blockquote: (props) => {
                            const isWarning = JSON.stringify(props.children).includes(
                                "Warning",
                            );
                            return (
                                <blockquote className={isWarning ? warning : undefined}>
                                    {props.children}
                                </blockquote>
                            );
                        },
                        code: ({inline, className, children, ...props}) => {
                            const match = /language-(\w+)/.exec(className ?? "");

                            if (inline !== true) {
                                const language =
                                    match != null ? (match[1] as "tsx") : undefined;
                                return (
                                    <Code language={language}>
                                        {String(children).replace(/\n$/, "")}
                                    </Code>
                                );
                            }
                            return (
                                <code className={cx(inlineCode, className)} {...props}>
                                    {children}
                                </code>
                            );
                        },
                    }}
                >
                    {props.content}
                </ReactMarkdown>
            </div>
        </div>
    </Layout>
);
