#!/usr/bin/env node

import fs from "fs";
import * as generated from "./generated";
import {promises as fsPromises} from "fs";

// Must be above the compile import as get-stdin used by
// json-schema-to-typescript messes up the descriptor even if unused.
const stdinBuffer = fs.readFileSync(0);

const {compile} = await import("json-schema-to-typescript");

import {
    Project,
    VariableDeclarationKind,
    InterfaceDeclarationStructure,
    OptionalKind,
} from "ts-morph";

const schema = JSON.parse(stdinBuffer.toString("utf8"));
const {urls: possibleEmptyUrls, templates, interfaces, types} = schema;

const urls: generated.Types["URLSchema"] = {
    ...possibleEmptyUrls,
    __reactivated_do_not_use: {
        route: "__reactivated_do_not_use",
        args: {},
    },
    __reactivated_do_not_use_args: {
        route: "__reactivated_do_not_use_args",
        args: {
            _: "string",
        },
    },
};

const project = new Project();

const sourceFile = project.createSourceFile("types");
const urlFile = project.createSourceFile("urls");

if (Object.keys(urls).length == 0) {
    urlFile.addStatements(`export const reverse () => throw new Error("No urls")`);
} else {
    urlFile.addVariableStatement({
        declarationKind: VariableDeclarationKind.Const,
        declarations: [
            {
                name: "urls",
                initializer: JSON.stringify(urls),
            },
        ],
    });

    const urlMap = {
        name: "URLMap",
        properties: [] as any,
        // isExported: true,
    };

    const withArguments = [""];

    const withoutArguments = [""];

    const interfaces: OptionalKind<InterfaceDeclarationStructure>[] = [urlMap];

    for (const name of Object.keys(urls)) {
        const properties = urls[name as keyof typeof urls].args;
        const normalizedName = name.replace(/[^\w]/g, "_");

        interfaces.push(
            ...[
                {
                    name: normalizedName,
                    properties: [
                        {name: "name", type: `'${name}'`},
                        {name: "args", type: `${normalizedName}_args`},
                    ],
                },
                {
                    name: `${normalizedName}_args`,

                    properties: Object.keys(properties).map((propertyName) => ({
                        name: propertyName,
                        type: properties[propertyName as keyof typeof properties],
                    })),
                },
            ],
        );

        urlMap.properties.push({
            name: normalizedName,
            type: normalizedName,
        });

        if (Object.keys(properties).length === 0) {
            withoutArguments.push(normalizedName);
        } else {
            withArguments.push(normalizedName);
        }
    }
    urlFile.addInterfaces(interfaces);
    urlFile.addTypeAlias({name: "WithArguments", type: withArguments.join("|")});
    urlFile.addTypeAlias({
        name: "WithoutArguments",
        type: withoutArguments.join("|"),
    });
    urlFile.addStatements(`

    type All = WithArguments|WithoutArguments;
    export function reverse<T extends WithoutArguments['name']>(name: T): string;
    export function reverse<T extends WithArguments['name']>(name: T, args: Extract<WithArguments, {name: T}>['args']): string;
    export function reverse<T extends All['name']>(name: T, args?: Extract<WithArguments, {name: T}>['args']): string {
        let route = urls[name].route;

        if (args != null) {
            for (const token of Object.keys(args)) {
                route = route.replace(new RegExp('<(.+?:)' + token + '>'), (args as any)[token]);
            }
        }
        return route;
    }`);
}

sourceFile.addStatements(
    "export type UUID = `${string}-${string}-${string}-${string}-${string}`;",
);

// reactivate/reactivateAdmin are declared AMBIENT: tsc sees the exports (so
// `import {reactivate} from "@reactivated"` type-checks in app source) but NO
// runtime import of "reactivated/dist/client" is emitted. @reactivated is
// imported by every app module; a value import of the framework client would
// drag it - and, via virtual:reactivated/templates, the app templates - into
// the shared graph, forming a cycle that breaks react-refresh (scene edits
// remount the whole app). The reactivated Vite plugin rewrites these two names
// to come from "reactivated/dist/client" at runtime, only in the (entry)
// modules that import them.
sourceFile.addStatements(`
import type {ReactivateConfig as GenericReactivateConfig} from "reactivated/dist/client";
export type ReactivateConfig = GenericReactivateConfig<_Types["Context"]>;
export declare const reactivate: (config?: ReactivateConfig) => void;
export declare const reactivateAdmin: () => void;

export const rpc = {requester: typeof window != "undefined" ? rpcUtils.defaultRequester : null as any};
import React from "react"
import * as generated from "reactivated/dist/generated";
import * as rpcUtils from "reactivated/dist/rpc";

export function classNames(...classes: (string | undefined | null | false)[]) {
    return classes.filter(Boolean).join(" ");
}

// Note: this needs strict function types to behave correctly with excess properties etc.
export type Checker<P, U extends (React.FunctionComponent<P> | React.ComponentClass<P>)> = {};

export {Context} from "./context";
import {Context} from "./context";
export {reverse} from "./urls";

export const Provider = (props: {value: _Types["Context"]; children: React.ReactNode}) => {
    const [value, setValue] = React.useState(props.value);

    return (
        <Context.Provider value={{...value, setValue}}>
            {props.children}
        </Context.Provider>
    );
};

export const getServerData = () => {
    const props: Record<string, unknown> = (window as any).__PRELOADED_PROPS__;
    const context: _Types["Context"] = (window as any).__PRELOADED_CONTEXT__;

    return {props, context};
};


export * as forms from "./forms";
`);

const formsContent = `
export {
    Form,
    FormSet,
    ManagementForm,
    Widget,
    useForm,
    useFormSet,
} from "reactivated/dist/forms";

import type {_Types} from "./index";
import * as forms from "reactivated/dist/forms";

import {Context} from "./context";
export const CSRFToken = forms.createCSRFToken(Context);

export const {createRenderer, Iterator} = forms.bindWidgetType<_Types["globals"]["Widget"]>();
export type FieldHandler = forms.FieldHandler<_Types["globals"]["Widget"]>;
export type {FormHandler} from "reactivated/dist/forms";
`;

const contextContent = `
/* eslint-disable */
import React from "react";

import type {_Types} from "./index"

type TContext = _Types["Context"];

type TMutableContext = TContext & {
    setValue: React.Dispatch<React.SetStateAction<TContext>>;
};

export const Context = React.createContext<TMutableContext>(null!);
`;

// tslint:disable-next-line
compile(types, "this is unused", {additionalProperties: false}).then(async (ts) => {
    process.stdout.write("/* eslint-disable */\n");
    // Needs to be on top, needed for vite typing of import.meta without work
    // by the downstream apps.
    process.stdout.write(`/// <reference types="vite/client.d.ts" />`);
    process.stdout.write(ts);
    const statements = [];

    if (!fs.existsSync("./reactivated-skip-template-check")) {
        for (const name of Object.keys(templates)) {
            const propsName = templates[name];

            statements.push(`

import {Template as ${name}Implementation} from "@client/templates/${name}"
export type ${name}Check = Checker<_Types["${propsName}"], typeof ${name}Implementation>;

export namespace templates {
    export type ${name} = _Types["${propsName}"];
}


        `);
        }
    }

    for (const name of Object.keys(interfaces)) {
        const propsName = interfaces[name];
        statements.push(`

export namespace interfaces {
    export type ${name} = _Types["${propsName}"];
}


        `);
    }

    sourceFile.addStatements(statements);

    process.stdout.write(sourceFile.getText());

    fs.mkdirSync("./client/generated", {recursive: true});

    await fsPromises.writeFile(
        "./client/generated/context.tsx",
        contextContent,
        "utf-8",
    );
    await fsPromises.writeFile("./client/generated/forms.tsx", formsContent, "utf-8");
    await fsPromises.writeFile(
        "./client/generated/urls.tsx",
        "/* eslint-disable */\n" + urlFile.getText(),
        "utf-8",
    );
});
