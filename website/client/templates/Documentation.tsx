import React from "react";

import {classNames, templates} from "@reactivated";
import {Helmet} from "react-helmet-async";
import ReactMarkdown from "react-markdown";

import {Code} from "@client/components/Code";
import {Layout} from "@client/components/Layout";
import * as styles from "@client/styles.css";

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
        <label className={styles.Hamburger} htmlFor="menu">
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
        <aside className={styles.Menu}>
            <Hamburger />
            <input
                type="checkbox"
                id="menu"
                style={{
                    display: "none",
                }}
            />
            <ul className={styles.menu}>
                <li>
                    <h1>
                        <a
                            href="/"
                            style={{
                                color: styles.colors.header,
                                textDecoration: "none",
                            }}
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
                            style={{
                                paddingLeft: 8,
                                borderColor: styles.colors.background,
                                borderLeftWidth: 3,
                                borderLeftStyle: "solid",
                                ...(href == props.path
                                    ? {
                                          borderColor: styles.colors.textWithColor,
                                      }
                                    : {}),
                            }}
                        >
                            <a
                                style={{
                                    color: styles.colors.header,
                                }}
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
            <div className={styles.documentationLayout}>
                <Menu {...props} />
                <div className={styles.Documentation}>
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
                                        className={
                                            isWarning ? styles.warning : undefined
                                        }
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
                                        className={classNames(
                                            styles.inlineCode,
                                            className,
                                        )}
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
                        style={{
                            paddingTop: 30,
                            paddingRight: 30,
                            width: 250,
                        }}
                        className={styles.hideOnMobile}
                    >
                        <ReactMarkdown
                            className={styles.ReactMarkdown}
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
