import React from "react";

import {templates} from "@reactivated";
import {Helmet} from "react-helmet-async";
import ReactMarkdown from "react-markdown";

import {css, cx} from "@linaria/core";

import {Code} from "@client/components/Code";
import {Layout} from "@client/components/Layout";
import * as styles from "@client/oldStyles";

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

const menu = css`
    ${styles.style({
        display: "flex",
        flexDirection: "column",
        flex: 1,
        gap: 20,
        marginLeft: 20,
        fontSize: 17,
        $mobile: {
            marginLeft: -10,
            alignItems: "center",
            gap: 10,
        },
    })}
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

        #menu:not(:checked) ~ .${menu} {
            ${styles.style({
                $mobile: {
                    display: "none !important",
                },
            })}
        }
    }
`;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const getAnchor = (children: any) => {
    const heading: string = // eslint-disable-line
        (children as any)?.[0]?.props?.children?.[0] ?? children?.[0] ?? ""; // eslint-disable-line

    // Brittle and doesn't always work.
    // const keepDots: boolean = children?.[0]?.type === "code";
    const keepDots: boolean = JSON.stringify(children).includes("code");
    const regex = keepDots === true ? /[^.a-zA-Z0-9 ]/g : /[^a-zA-Z0-9 ]/g;
    const anchor = heading.toLowerCase().replace(regex, "").replace(/\s+/g, "-");

    return anchor;
};

export const Hamburger = () => {
    return (
        <label
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
            htmlFor="menu"
        >
            <svg
                xmlns="http://www.w3.org/2000/svg"
                width="2em"
                height="2em"
                viewBox="0 0 20 20"
            >
                <path d="M17.5 6h-15a.5.5 0 010-1h15a.5.5 0 010 1zM17.5 11h-15a.5.5 0 010-1h15a.5.5 0 010 1zM17.5 16h-15a.5.5 0 010-1h15a.5.5 0 010 1z" />
            </svg>
        </label>
    );
};

const Menu = (props: templates.Documentation) => {
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
            <Hamburger />
            <input
                type="checkbox"
                id="menu"
                className={css`
                    ${styles.style({display: "none"})}
                `}
            />
            <ul className={menu}>
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

export default (props: templates.Documentation) => {
    const headings = props.content.match(/#{2,6}.+(?=\n)/g)?.join("\n");

    return (
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
                            h2: ({children}) => {
                                const anchor = getAnchor(children);

                                return <h2 id={anchor}>{children}</h2>;
                            },
                            h3: ({children}) => {
                                const anchor = getAnchor(children);

                                return <h3 id={anchor}>{children}</h3>;
                            },
                            blockquote: (props) => {
                                const isWarning = JSON.stringify(
                                    props.children,
                                ).includes("Warning");
                                return (
                                    <blockquote
                                        className={isWarning ? warning : undefined}
                                    >
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
                                    <code
                                        className={cx(inlineCode, className)}
                                        {...props}
                                    >
                                        {children}
                                    </code>
                                );
                            },
                        }}
                    >
                        {props.content}
                    </ReactMarkdown>
                </div>
                {headings != null && (
                    <div
                        className={css`
                            ${styles.style({
                                paddingTop: 30,
                                paddingRight: 30,
                                width: 250,
                                $mobile: {display: "none"},
                            })}
                        `}
                    >
                        <ReactMarkdown
                            className={css`
                                ${styles.style({
                                    display: "flex",
                                    flexDirection: "column",
                                    position: "sticky",
                                    top: 30,
                                    gap: 10,
                                    $nest: {
                                        a: {
                                            textDecoration: "none",
                                        },
                                        "h2 a": {
                                            color: styles.colors.header,
                                        },
                                        h2: {
                                            color: styles.colors.header,
                                            fontSize: 18,
                                        },
                                        "h3 a": {
                                            color: styles.colors.textWithColor,
                                        },
                                        h3: {
                                            fontFamily: "inherit",
                                            fontSize: 16,
                                            color: styles.colors.textWithColor,
                                        },
                                    },
                                })}
                            `}
                            components={{
                                h2: ({children}) => {
                                    const anchor = getAnchor(children);

                                    return (
                                        <h2>
                                            <a href={`#${anchor}`}>{children}</a>
                                        </h2>
                                    );
                                },
                                h3: ({children}) => {
                                    const anchor = getAnchor(children);

                                    return (
                                        <h3>
                                            <a href={`#${anchor}`}>{children}</a>
                                        </h3>
                                    );
                                },
                            }}
                        >
                            {headings}
                        </ReactMarkdown>
                    </div>
                )}
            </div>
        </Layout>
    );
};
