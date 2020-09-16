import fs from "fs";
import {compile} from "json-schema-to-typescript";
import {
    Project,
    SourceFile,
    StructureKind,
    SyntaxKind,
    VariableDeclarationKind,
    WriterFunction,
} from "ts-morph";

const stdinBuffer = fs.readFileSync(0); // STDIN_FILENO = 0

const schema = JSON.parse(stdinBuffer.toString("utf8"));
const {urls, templates, types} = schema;

import {NormalModuleReplacementPlugin} from "webpack";

const project = new Project();

/*
const urls = {
    'widget_list': {'widget_id': 'number', 'category_id': 'string'},
    'create_widget': {},
    'widget_detail': {'pk': 'number'},
};
*/
const interfaces = project.createSourceFile("");

interfaces.addVariableStatement({
    declarationKind: VariableDeclarationKind.Const,
    declarations: [
        {
            name: "urls",
            initializer: JSON.stringify(urls),
        },
    ],
});

const urlMap = interfaces.addInterface({
    name: "URLMap",
});
urlMap.setIsExported(true);

const withArguments = [];
const withoutArguments = [];

for (const name of Object.keys(urls)) {
    const properties = urls[name as keyof typeof urls].args;
    const normalizedName = name.replace(/[^\w]/g, "_");

    const urlInterface = interfaces.addInterface({
        name: normalizedName,
        properties: [{name: "name", type: `'${name}'`}],
    });
    const argsInterface = interfaces.addInterface({
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
interfaces.addTypeAlias({name: "WithArguments", type: withArguments.join("|")});
interfaces.addTypeAlias({name: "WithoutArguments", type: withoutArguments.join("|")});
interfaces.addStatements(`

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

// project.save();
// const result = project.emitToMemory();
// project.emi

interfaces.addStatements(`
import React from "react"
import * as widgets from "reactivated/components/Widget";

// Note: this needs strict function types to behave correctly with excess properties etc.
export type Checker<P, U extends (React.FunctionComponent<P> | React.ComponentClass<P>)> = {};

`);

// tslint:disable-next-line
compile(types, "Types").then((ts) => {
    process.stdout.write("/* tslint:disable */\n");
    process.stdout.write(ts);

    for (const name of Object.keys(templates)) {
        const propsName = templates[name];
        interfaces.addStatements(`

import ${name}Implementation from "@client/templates/${name}"
export type ${name}Check = Checker<Types["${propsName}"], typeof ${name}Implementation>;


        `);
    }
    process.stdout.write(interfaces.getText());
});
