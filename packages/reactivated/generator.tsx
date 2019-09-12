import {Project, StructureKind, VariableDeclarationKind, WriterFunctions, SourceFile} from "ts-morph";
import fs from 'fs';

const stdinBuffer = fs.readFileSync(0); // STDIN_FILENO = 0

const urls = JSON.parse(stdinBuffer.toString('utf8'));

import { NormalModuleReplacementPlugin } from "webpack";

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
    declarations: [{
        name: 'urls',
        initializer: JSON.stringify(urls),
    }],
})

const urlMap = interfaces.addInterface({
    name: 'URLMap',
});

const withArguments = [];
const withoutArguments = [];

for (const name of Object.keys(urls)) {
    const properties = urls[name as keyof typeof urls]['args'];
    const normalizedName = name.replace(/[^\w]/g, '_');

    const urlInterface = interfaces.addInterface({
        name: normalizedName,
        properties: [
            {name: 'name', type: `'${name}'`},
        ],
    });
    const argsInterface = interfaces.addInterface({
        name: `${normalizedName}_args`,
    })

    for (const propertyName of Object.keys(properties)) {
        argsInterface.addProperty({
            name: propertyName,
            type: properties[propertyName as keyof typeof properties],
        });
    }
    urlInterface.addProperty({
        name: 'args',
        type: `${normalizedName}_args`,
    })

    urlMap.addProperty({
        name: normalizedName,
        type: normalizedName,
    });

    if (Object.keys(properties).length === 0) {
        withoutArguments.push(normalizedName);
    }
    else {
        withArguments.push(normalizedName);
    }
}
interfaces.addTypeAlias({name: 'WithArguments', type: withArguments.join('|')});
interfaces.addTypeAlias({name: 'WithoutArguments', type: withoutArguments.join('|')});
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
process.stdout.write(interfaces.getText());

interface First {
    name: 'foo';
    args: {
        uuid: string;
    }
}

interface Second {
    name: 'bar';
    args: {
        pk: number;
    }
}

interface Third {
    name: 'spam';
}

interface Fourth {
    name: 'ham';
}

type WithArguments = First|Second;
type WithoutArguments = Third|Fourth;
type All = WithArguments|WithoutArguments;
type UnionKeys<T> = T extends any ? keyof T : never
type DistributivePick<T, K extends UnionKeys<T>> = T extends any ? Pick<T, Extract<keyof T, K>> : never;


export function reverse<T extends WithoutArguments['name']>(name: T): void;
export function reverse<T extends WithArguments['name']>(name: T, args: Extract<WithArguments, {name: T}>['args']): void;
export function reverse<T extends All['name']>(name: T, args?: Extract<WithArguments, {name: T}>['args']): void {
}

reverse('foo', {uuid: 'a'});
reverse('bar', {pk: 1});
reverse('spam');
reverse('ham');
