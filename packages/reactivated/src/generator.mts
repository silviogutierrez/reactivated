#!/usr/bin/env node

import fs from "fs";
import * as generated from "./generated";

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

const sourceFile = project.createSourceFile("");

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

if (Object.keys(urls).length !== 0) {
    sourceFile.addVariableStatement({
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
    sourceFile.addInterfaces(interfaces);
    sourceFile.addTypeAlias({name: "WithArguments", type: withArguments.join("|")});
    sourceFile.addTypeAlias({
        name: "WithoutArguments",
        type: withoutArguments.join("|"),
    });
    sourceFile.addStatements(`

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
// For import.meta to be typed.
import "vite/client";

export type {Options} from "reactivated/dist/conf";
export type {Renderer} from "reactivated/dist/render.mjs";


export const rpc = new RPC(typeof window != "undefined" ? rpcUtils.defaultRequester : null as any);
import React from "react"
import createContext from "reactivated/dist/context";
import * as forms from "reactivated/dist/forms";
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

export const {Context, Provider, getServerData} = createContext<_Types["Context"]>();

export const viteGetTemplate = async ({template_name}: {template_name: string}) => {
    // This require needs to be *inside* the function to avoid circular dependencies with esbuild.
    // No {eager: true}) to import.meta.glob as you get weird circular initialization issues.
    // @ts-ignore
    const templates = import.meta.glob("@client/templates/*.tsx");

    const templatePath = \`/client/templates/\${template_name}.tsx\`;

    const TemplateModule = await templates[templatePath]() as {Template: React.ComponentType<any>}
    return TemplateModule.Template;
}

export const getTemplate = ({template_name}: {template_name: string}) => {
    // This require needs to be *inside* the function to avoid circular dependencies with esbuild.
    const { default: templates, filenames } = require('../../client/templates/**/*');
    const templatePath = "../../client/templates/" + template_name + ".tsx";
    const possibleTemplate: {default: React.ComponentType<any>} | null = templates.find((t: any, index: number) => filenames[index] === templatePath);

    if (possibleTemplate == null) {
        throw new Error("Template " + template_name + ".tsx not found");
    }
    return possibleTemplate.default;
}

export const CSRFToken = forms.createCSRFToken(Context);

export const {createRenderer, Iterator} = forms.bindWidgetType<_Types["globals"]["Widget"]>();
export type FieldHandler = forms.FieldHandler<_Types["globals"]["Widget"]>;
export type models = _Types["globals"]["models"];

export type {FormHandler} from "reactivated/dist/forms";
export const {Form, FormSet, Widget, useForm, useFormSet, ManagementForm} = forms;
`);

// tslint:disable-next-line
compile(types, "this is unused").then((ts) => {
    process.stdout.write("/* eslint-disable */\n");
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
});
