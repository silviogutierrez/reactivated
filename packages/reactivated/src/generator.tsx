#!/usr/bin/env node

import fs from "fs";
import * as generated from "./generated";

// Must be above the compile import as get-stdin used by
// json-schema-to-typescript messes up the descriptor even if unused.
const stdinBuffer = fs.readFileSync(0);

import {compile} from "json-schema-to-typescript";
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

const classDeclaration = sourceFile.addClass({
    name: "RPC",
    isExported: true,
});

const rpcConstructor = classDeclaration.addConstructor({
    parameters: [{name: "requester", type: "rpcUtils.Requester", scope: Scope.Public}],
});

let rpcConstructorBody = "";

for (const name of Object.keys(rpc)) {
    const {url, input, output, type, params} = rpc[name];
    const functionDeclaration = classDeclaration.addMethod({
        name,
    });

    rpcConstructorBody += `this.${name} = (this.${name} as any).bind(this);\n`;
    functionDeclaration.setIsAsync(true);

    functionDeclaration.addParameter({
        name: "this",
        type: "void",
    });

    let bodyText = "";
    const initializer = {
        url: (writer: CodeBlockWriter) => writer.quote(url),
        name: (writer: CodeBlockWriter) => writer.quote(name),
    };

    if (params.length >= 1) {
        const paramsInterface = functionDeclaration.addInterface({
            name: "WILL_BE_STRIPPED",
        });

        const iterator = [];
        for (const [paramType, paramName] of params) {
            paramsInterface.addProperty({name: paramName, type: "string | number"});
            iterator.push(paramName);
        }
        functionDeclaration.addParameter({
            name: "params",
            type: paramsInterface.getText().replace("interface WILL_BE_STRIPPED", ""),
        });

        Object.assign(initializer, {
            paramsAndIterator: Writers.object({
                iterator: JSON.stringify(iterator),
                params: "params",
            }),
        });
        // Otherwise our interface will be inserted.
        functionDeclaration.setBodyText("");
    } else {
        Object.assign(initializer, {paramsAndIterator: "null"});
    }

    if (input != null) {
        const property = classDeclaration.addProperty({
            // isStatic: true,
            name: input,
            type: `_Types["${input}"]`,
            initializer: JSON.stringify(values[input]),
        });
        functionDeclaration.addParameter({
            name: "input",
            type: `forms.FormOrFormSetValues<_Types["${input}"]>`,
        });
        functionDeclaration.setReturnType(
            `Promise<rpcUtils.Result<_Types["${output}"], forms.FormOrFormSetErrors<_Types["${input}"]>>>`,
        );
        Object.assign(initializer, {
            input: Writers.object({
                values: "input",
                type: (writer: CodeBlockWriter) =>
                    writer.quote(type).write(" as const"),
            }),
        });
    } else {
        functionDeclaration.setReturnType(
            `Promise<rpcUtils.Result<_Types["${output}"], null>>`,
        );
        Object.assign(initializer, {input: "null"});
    }

    functionDeclaration.addVariableStatement({
        declarationKind: VariableDeclarationKind.Const,
        declarations: [
            {
                name: "options",
                initializer: Writers.object(initializer),
                /*
                    x: 123,
                    y: (writer) => writer.quote("abc"),
                    z: Writers.object({
                        one: (writer) => writer.quote("1"),
                    }),
                    */
            },
        ],
    });
    functionDeclaration.setBodyText(
        `${functionDeclaration.getBodyText()} return rpcUtils.rpcCall((this as any).requester, options)`,
    );
    /*

    if (input != null) {
        functionDeclaration.addParameter({
            name: "input",
            type: `forms.FormOrFormSetValues<_Types["${input}"]>`,
        });
        bodyText = bodyText.concat(`
        const input = ${JSON.stringify({
            type: "form",
        })};
        }
        `);
    }
    else {
    }
    */

    /*
     if (instance.length === 1) {
        functionDeclaration.addParameter({name: "instance", type: `string | number`});
        functionDeclaration.setBodyText(`return rpcUtils.rpcCall("${url}", input, "${type}", instance)`);
     }
     else if (instance.length >= 2) {
        const instanceInterface = functionDeclaration.addInterface({name: "WILL_BE_STRIPPED"});

        for (const instanceArg of instance) {
            instanceInterface.addProperty({name: instanceArg, type: "string | number"});
        }
        functionDeclaration.addParameter({name: "instance", type: instanceInterface.getText().replace("interface WILL_BE_STRIPPED", "")});
        functionDeclaration.setBodyText(`const iterator = ${JSON.stringify(instance)}; return rpcUtils.rpcCall("${url}", input, "${type}", {iterator, params: instance})`);
     }
     else {
        functionDeclaration.setBodyText(`return rpcUtils.rpcCall("${url}", input, "${type}")`);
     }

     functionDeclaration.addParameter({name: "input", type: `forms.FormOrFormSetValues<_Types["${input}"]>`});
     functionDeclaration.setReturnType(`Promise<rpcUtils.Result<_Types["${output}"], forms.FormOrFormSetErrors<_Types["${input}"]>>>`);
     functionDeclaration.setIsAsync(true);
     */
}
rpcConstructor.setBodyText(rpcConstructorBody);

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

    const urlMap = sourceFile.addInterface({
        name: "URLMap",
    });
    urlMap.setIsExported(true);

    const withArguments = [""];
    const withoutArguments = [""];

    for (const name of Object.keys(urls)) {
        const properties = urls[name as keyof typeof urls].args;
        const normalizedName = name.replace(/[^\w]/g, "_");

        const urlInterface = sourceFile.addInterface({
            name: normalizedName,
            properties: [{name: "name", type: `'${name}'`}],
        });
        const argsInterface = sourceFile.addInterface({
            name: `${normalizedName}_args`,
        });

        for (const propertyName of Object.keys(properties)) {
            argsInterface.addProperty({
                name: propertyName,
                type: properties[propertyName as keyof typeof properties],
            });
        }
        urlInterface.addProperty({
            name: "args",
            type: `${normalizedName}_args`,
        });

        urlMap.addProperty({
            name: normalizedName,
            type: normalizedName,
        });

        if (Object.keys(properties).length === 0) {
            withoutArguments.push(normalizedName);
        } else {
            withArguments.push(normalizedName);
        }
    }
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

sourceFile.addStatements(`
export const rpc = new RPC(typeof window != "undefined" ? rpcUtils.defaultRequester : null as any);
import React from "react"
import createContext from "reactivated/dist/context";
import * as forms from "reactivated/dist/forms";
import * as generated from "reactivated/dist/generated";
import * as rpcUtils from "reactivated/dist/rpc";

// Note: this needs strict function types to behave correctly with excess properties etc.
export type Checker<P, U extends (React.FunctionComponent<P> | React.ComponentClass<P>)> = {};

export const {Context, Provider, getServerData} = createContext<_Types["Context"]>();

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

export {FormHandler} from "reactivated/dist/forms";
export const {Form, FormSet, Widget, useForm, useFormSet, ManagementForm} = forms;
`);

// tslint:disable-next-line
compile(types, "_Types").then((ts) => {
    process.stdout.write("/* eslint-disable */\n");
    process.stdout.write(ts);

    if (!fs.existsSync("./reactivated-skip-template-check")) {
        for (const name of Object.keys(templates)) {
            const propsName = templates[name];

            sourceFile.addStatements(`

import ${name}Implementation from "@client/templates/${name}"
export type ${name}Check = Checker<_Types["${propsName}"], typeof ${name}Implementation>;

export namespace templates {
    export type ${name} = _Types["${propsName}"];
}


        `);
        }
    }

    for (const name of Object.keys(interfaces)) {
        const propsName = interfaces[name];
        sourceFile.addStatements(`

export namespace interfaces {
    export type ${name} = _Types["${propsName}"];
}


        `);
    }

    process.stdout.write(sourceFile.getText());
});
