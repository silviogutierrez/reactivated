#!/usr/bin/env node

import fs from "fs";
import * as generated from "./generated";
import {promises as fsPromises} from "fs";

// Must be above the compile import as get-stdin used by
// json-schema-to-typescript messes up the descriptor even if unused.
const stdinBuffer = fs.readFileSync(0);

const {compile} = await import("json-schema-to-typescript");

import {
    CodeBlockWriter,
    Project,
    Scope,
    SourceFile,
    StructureKind,
    SyntaxKind,
    VariableDeclarationKind,
    WriterFunction,
    Writers,
    InterfaceDeclarationStructure,
    OptionalKind,
    MethodDeclarationStructure,
    PropertyDeclarationStructure,
    ParameterDeclarationStructure,
    StatementedNodeStructure,
    StatementStructures,
} from "ts-morph";

const schema = JSON.parse(stdinBuffer.toString("utf8"));
const {
    urls: possibleEmptyUrls,
    templates,
    interfaces,
    rpc: uncastedRpc,
    types,
    values,
} = schema;

const rpc: generated.Types["RPCRegistry"] = uncastedRpc;

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

const rpcConstructorStructure = {
    statements: [] as string[],
    parameters: [
        {
            name: "requester",
            type: "rpcUtils.Requester",
            isReadonly: false,
            scope: Scope.Public,
            decorators: [],
            hasQuestionToken: false,
            hasOverrideKeyword: false,
            kind: StructureKind.Parameter as const,
            isRestParameter: false,
        },
    ],
    typeParameters: [],
    docs: [],
    kind: StructureKind.Constructor as const,
    overloads: [],
};

const rpcStructure = {
    decorators: [],
    typeParameters: [],
    docs: [],
    isAbstract: false,
    implements: [],
    name: "RPC",
    isExported: true,
    isDefaultExport: false,
    hasDeclareKeyword: false,
    kind: StructureKind.Class as const,
    ctors: [rpcConstructorStructure],
    properties: [] as OptionalKind<PropertyDeclarationStructure>[],
    methods: [] as OptionalKind<MethodDeclarationStructure>[],
};

for (const name of Object.keys(rpc)) {
    const {url, input, output, type, params} = rpc[name];

    const methodStructure = {
        kind: StructureKind.Method as const,
        name,
        isAsync: true,
        parameters: [] as OptionalKind<ParameterDeclarationStructure>[],
        statements: [] as (string | StatementStructures)[],
        returnType: "",
    };

    rpcConstructorStructure.statements.push(
        `this.${name} = (this.${name} as any).bind(this);\n`,
    );

    methodStructure.parameters?.push({
        name: "this",
        type: "void",
    });

    let bodyText = "";
    const initializer = {
        url: (writer: CodeBlockWriter) => writer.quote(url),
        name: (writer: CodeBlockWriter) => writer.quote(name),
    };

    if (params.length >= 1) {
        const paramsProperties = [];

        const iterator = [];
        for (const [paramType, paramName] of params) {
            paramsProperties.push({name: paramName, type: "string | number"});
            iterator.push(paramName);
        }
        methodStructure.parameters?.push({
            name: "params",
            type: Writers.objectType({properties: paramsProperties}),
            isReadonly: false,
            decorators: [],
            hasQuestionToken: false,
            hasOverrideKeyword: false,
            kind: StructureKind.Parameter as const,
            isRestParameter: false,
        });

        Object.assign(initializer, {
            paramsAndIterator: Writers.object({
                iterator: JSON.stringify(iterator),
                params: "params",
            }),
        });
    } else {
        Object.assign(initializer, {paramsAndIterator: "null"});
    }

    if (input != null) {
        rpcStructure.properties?.push({
            name: input,
            type: `_Types["${input}"]`,
            initializer: JSON.stringify(values[input]),
        });
        methodStructure.parameters?.push({
            name: "input",
            type: `forms.FormOrFormSetValues<_Types["${input}"]>`,
        });

        methodStructure.returnType = `Promise<rpcUtils.Result<_Types["${output}"], forms.FormOrFormSetErrors<_Types["${input}"]>, _Types["RPCPermission"]>>`;

        Object.assign(initializer, {
            input: Writers.object({
                values: "input",
                type: (writer: CodeBlockWriter) =>
                    writer.quote(type).write(" as const"),
            }),
        });
    } else {
        methodStructure.returnType = `Promise<rpcUtils.Result<_Types["${output}"], null, _Types["RPCPermission"]>>`;
        Object.assign(initializer, {input: "null"});
    }

    methodStructure.statements?.push({
        kind: StructureKind.VariableStatement,
        declarationKind: VariableDeclarationKind.Const,
        declarations: [
            {
                name: "options",
                initializer: Writers.object(initializer),
            },
        ],
    });
    methodStructure.statements?.push(
        "return rpcUtils.rpcCall((this as any).requester, options)",
    );
    rpcStructure.methods?.push(methodStructure);
}

sourceFile.addClass(rpcStructure);

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

sourceFile.addStatements(`
import type {Renderer as GenericRenderer} from "reactivated/dist/render.mjs";
export type Renderer = GenericRenderer<_Types["Context"]>;

export const rpc = new RPC(typeof window != "undefined" ? rpcUtils.defaultRequester : null as any);
import React from "react"
import * as generated from "reactivated/dist/generated";
import * as rpcUtils from "reactivated/dist/rpc";
import {constants} from "./constants";
export {constants};

export function classNames(...classes: (string | undefined | null | false)[]) {
    return classes.filter(Boolean).join(" ");
}

// Note: this needs strict function types to behave correctly with excess properties etc.
export type Checker<P, U extends (React.FunctionComponent<P> | React.ComponentClass<P>)> = {};

export type Result<TSuccess, TInvalid> = rpcUtils.Result<TSuccess, TInvalid, _Types["RPCPermission"]>;

export {Context} from "./context";
import {Context} from "./context";

import * as forms from "reactivated/dist/forms";
export type {FormHandler} from "reactivated/dist/forms";
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

export type models = _Types["globals"]["models"];

export type {FieldHandler} from "./forms";
export {Form, FormSet, Widget, useForm, useFormSet, ManagementForm} from "reactivated/dist/forms";
export {Iterator, CSRFToken, createRenderer} from "./forms";
${"REACTIVATED_NO_GET_TEMPLATE" in process.env ? "" : `export {getTemplate} from "./template";`}
`);

const formsContent = `
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

const templateContent = `
// @ts-ignore
const templates = import.meta.glob("@client/templates/*.tsx", {eager: true});

export const getTemplate = async ({template_name}: {template_name: string}) => {
    const templatePath = \`/client/templates/\${template_name}.tsx\`;
    const TemplateModule = templates[templatePath] as {Template: React.ComponentType<any>}
    return TemplateModule.Template;
}
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

    await fsPromises.writeFile(
        "./node_modules/_reactivated/context.tsx",
        contextContent,
        "utf-8",
    );
    await fsPromises.writeFile(
        "./node_modules/_reactivated/forms.tsx",
        formsContent,
        "utf-8",
    );
    await fsPromises.writeFile(
        "./node_modules/_reactivated/urls.tsx",
        "/* eslint-disable */\n" + urlFile.getText(),
        "utf-8",
    );
    await fsPromises.writeFile(
        "./node_modules/_reactivated/template.tsx",
        templateContent,
        "utf-8",
    );
});
