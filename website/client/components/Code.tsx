import React from "react";

// This doesn't work with SSR, Probably because the specific languages are not
// registered when rendering with SSR, but are with the widnow.  So there is a
// text mistmatch.  Maybe: register dynamically. Or load dynamically.  Or void
// the mismatch error.
// import {Light as SyntaxHighlighter} from "react-syntax-highlighter";
// import tsx from "react-syntax-highlighter/dist/esm/languages/prism/tsx";
// import ts from "react-syntax-highlighter/dist/esm/languages/prism/typescript";
// SyntaxHighlighter.registerLanguage('tsx', tsx);
// SyntaxHighlighter.registerLanguage('ts', ts);
import {Prism as SyntaxHighlighter} from "react-syntax-highlighter";

// import ts from "react-syntax-highlighter/dist/esm/languages/prism/typescript";
import {nord as style} from "react-syntax-highlighter/dist/cjs/styles/prism";

interface Props {
    children: string | string[];
    language: "tsx" | "python" | "bash" | undefined;
}

export const Code = (props: Props) => (
    <div
        style={{
            maxWidth: "100%",
            overflow: "auto",
        }}
    >
        <SyntaxHighlighter
            language={props.language}
            style={
                style // eslint-disable-line @typescript-eslint/no-unsafe-assignment
            }
            customStyle={{fontSize: 14, borderRadius: 10}}
        >
            {props.children}
        </SyntaxHighlighter>
    </div>
);
